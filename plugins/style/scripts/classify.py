#!/usr/bin/env python3
"""UserPromptSubmit hook: a classifier grades the user's message in the TypeSafe.ai
answers format and glues a short directive to the prompt.

Request/response mirror https://docs.typesafe.ai/api (state + questions → answers).
The classifier is a backend from BACKENDS: `--model <name>`, else $STYLE_CLASSIFIER_BACKEND,
else claude. $STYLE_CLASSIFIER_MODEL overrides the backend's model id. Every call is
logged to ~/.claude/state/style-classifier/log.jsonl.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

TIMEOUT_S = 12
STATE_LIMIT = 6000  # chars per state field; more only costs tokens
LOG = Path.home() / ".claude/state/style-classifier/log.jsonl"
LOG_KEEP = 200  # rows; the full JSON of recent calls, enough for a Jev migration sample
ENV_FILE = Path.home() / ".claude/.env"  # TYPESAFE_API_KEY fallback, shared with jev-feedback

QUESTIONS = {
    "reply_mode": {
        "type": "choice",
        "instructions": "What kind of reply the user wants to user_message",
        "criteria": {
            "short": "a direct answer in a few lines, plain words, no code identifiers",
            "detailed": "the user explicitly asks for details, a full write-up, or a report",
            "trace": "how code works step by step; the user asks where/how in the code",
            "code": "write, change or fix code; implement something",
            "design": "think through an approach or options together; brainstorming",
        },
    },
    "max_lines": {
        "type": "score",
        "instructions": "How long the reply may be",
        "criteria": ["up to 3 lines", "up to 8 lines", "up to 20 lines", "no limit"],
    },
    "go_ahead": {
        "type": "noul",
        "instructions": "user_message explicitly tells to implement or change something now",
        "criteria": {
            "true": "asks for a change to be made now, politely or not: do it, implement, fix it, redo it, can you fix this, делай, переделывай, поправь",
            "false": "asks to explain or look at something, thinks out loud, weighs options, or describes future work without asking to start it",
        },
    },
    "prev_verdict": {
        "type": "choice",
        "instructions": "How user_message judges previous_answer. none when previous_answer is empty or user_message does not react to it",
        "criteria": {
            "liked": "explicit praise of previous_answer: отлично, супер, exactly this, perfect",
            "disliked": "complaint, correction, or 'redo' aimed at previous_answer",
            "none": "no judgement, a new question or topic, or plain acceptance like ok / давай / делаем",
        },
    },
    "prev_issue": {
        "type": "choice",
        "instructions": "If prev_verdict is disliked, what was wrong with previous_answer; otherwise none",
        "criteria": {
            "too_long": "too much text for the question asked",
            "jargon": "function names, classes, line numbers or internal vocabulary the user did not ask for",
            "off_question": "answered a neighbouring topic, not what was asked",
            "wrong_facts": "the content is wrong; default for 'это фигня, переделывай' without details",
            "unasked_options": "listed alternatives or caveats instead of one answer",
            "none": None,
        },
    },
}

SYSTEM = (
    "You are a System One classifier. You receive a JSON request with `state` and "
    "`questions` (types noul, choice, score). Answer every question. Output ONLY a JSON "
    "object {\"answers\": {...}} with, per question id:\n"
    "- noul: {\"type\":\"noul\",\"noul\":<0..1>}\n"
    "- choice: {\"type\":\"choice\",\"choice\":<option>,\"probabilities\":{option:p},\"confidence\":<0..1>}\n"
    "- score: {\"type\":\"score\",\"score\":<weighted level index>,\"legend\":{\"0\":...},"
    "\"probabilities\":{\"0\":p,...},\"confidence\":<0..1>}\n"
    "Probabilities sum to 1. No prose, no markdown fences."
)


def main(backend: str) -> None:
    if os.environ.get("STYLE_CLASSIFIER"):
        return
    hook = json.load(sys.stdin)
    prompt = hook.get("prompt", "").strip()
    if not prompt or prompt.startswith("/"):
        return
    previous_user, previous_answer = last_exchange(hook.get("transcript_path", ""))
    request = {
        "state": {
            "previous_user_message": previous_user[-STATE_LIMIT:],
            "previous_answer": previous_answer[-STATE_LIMIT:],
            "user_message": clip(prompt),
        },
        "questions": QUESTIONS,
    }
    started = time.time()
    answers = classify(backend, request)
    try:
        text = directive(answers, bool(previous_answer))
    except (KeyError, ValueError, TypeError, IndexError):
        text, answers = "", {}  # rejected answers are logged as FAILED, so /style:log never formats them
    log({"ts": time.strftime("%Y-%m-%d %H:%M"), "backend": backend, "request": request,
         "answers": answers, "ms": int((time.time() - started) * 1000)})
    if text:
        print(text)


def clip(text: str) -> str:
    """Head and tail of a long paste; the correction usually sits at the end."""
    if len(text) <= STATE_LIMIT:
        return text
    half = STATE_LIMIT // 2
    return text[:half] + "\n[... truncated ...]\n" + text[-half:]


def last_exchange(path: str) -> tuple[str, str]:
    """Last visible assistant text and the user message it answered."""
    user_text, answer = "", ""
    try:
        rows = Path(path).read_text().splitlines()
    except OSError:
        return user_text, answer
    pending_user = ""
    for line in rows:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("isMeta") or row.get("isCompactSummary") or row.get("isSidechain"):
            continue
        content = row.get("message", {}).get("content")
        if row.get("type") == "user":
            spoken = user_text_of(content)
            if spoken:
                pending_user = spoken
        elif row.get("type") == "assistant" and isinstance(content, list):
            texts = [b.get("text", "") for b in content if b.get("type") == "text"]
            if texts:
                user_text, answer = pending_user, "\n".join(texts)
    return user_text, answer


def user_text_of(content) -> str:
    """What the user typed: a plain string or text blocks; tool results are not speech."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if b.get("type") == "text")
    return ""


def classify(backend: str, request: dict) -> dict:
    call, parse, model = BACKENDS[backend]
    try:
        return parse(call(os.environ.get("STYLE_CLASSIFIER_MODEL") or model, request))
    except (subprocess.TimeoutExpired, ValueError, KeyError, TypeError, OSError):
        return {}


def run(cmd: list[str]) -> str:
    """stdout of a CLI call; a temp cwd keeps project instructions out of the classifier."""
    env = dict(os.environ, STYLE_CLASSIFIER="1")
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S, env=env,
                         stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir())
    return out.stdout


def call_claude(model: str, request: dict) -> str:
    return run(["claude", "-p", "--model", model,
                "--setting-sources", "", "--tools", "", "--no-session-persistence",
                "--output-format", "json", "--system-prompt", SYSTEM,
                json.dumps(request, ensure_ascii=False)])


def call_opencode(model: str, request: dict) -> str:
    # opencode run has no system-prompt flag: the rules go first in the message
    return run(["opencode", "run", "--pure", "-m", model,
                SYSTEM + "\n\n" + json.dumps(request, ensure_ascii=False)])


def call_pi(model: str, request: dict) -> str:
    return run(["pi", "-p", "--model", model, "--no-session", "-nt", "-ns", "-np",
                "--thinking", "off", "--system-prompt", SYSTEM,
                json.dumps(request, ensure_ascii=False)])


def typesafe_key() -> str:
    """$TYPESAFE_API_KEY, else its line in ~/.claude/.env."""
    if os.environ.get("TYPESAFE_API_KEY"):
        return os.environ["TYPESAFE_API_KEY"]
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("TYPESAFE_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise KeyError("TYPESAFE_API_KEY")


def call_jev(model: str, request: dict) -> str:
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=json.dumps({"model": model, **request}, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {typesafe_key()}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read().decode()


def parse_claude(raw: str) -> dict:
    """claude -p --output-format json wraps the model text in {"result": "..."}."""
    return parse_text(json.loads(raw)["result"])


def parse_text(raw: str) -> dict:
    """The {"answers": ...} object inside model text: fences, prose or a CLI header around it."""
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])["answers"]


def parse_jev(raw: str) -> dict:
    return json.loads(raw)["answers"]


# name → (call, parse, default model id)
BACKENDS = {
    "claude": (call_claude, parse_claude, "haiku"),
    "opencode": (call_opencode, parse_text, "opencode-go/deepseek-v4.1-flash"),
    "pi": (call_pi, parse_text, "opencode-go/deepseek-v4.1-flash"),
    "jev": (call_jev, parse_jev, "jev-latest"),
}


LENGTHS = QUESTIONS["max_lines"]["criteria"]
RUBRIC = {
    "short": "plain words, one answer, no function names or line numbers",
    "detailed": "full write-up, structure allowed",
    "trace": "execution order with file:line anchors, one hop per line",
    "code": "code first, then at most three lines on what was skipped",
    "design": "verdict first, then the few facts that change it, no option tours",
}


def directive(ans: dict, has_previous: bool) -> str:
    mode = pick(ans["reply_mode"], QUESTIONS["reply_mode"]["criteria"])
    length = LENGTHS[int(pick(ans["max_lines"], [str(i) for i in range(len(LENGTHS))]))]
    go = unit(ans["go_ahead"]["noul"])
    verdict = pick(ans["prev_verdict"], QUESTIONS["prev_verdict"]["criteria"])
    issue = pick(ans["prev_issue"], QUESTIONS["prev_issue"]["criteria"])
    if not has_previous:
        verdict = "none"
    if verdict != "disliked":
        issue = "none"
    lines = [f"[style] reply={mode}, {length}: {RUBRIC[mode]}."]
    if go >= 0.8:
        lines.append("[style] user said do it: implement, do not ask again.")
    elif go >= 0.4:
        lines.append("[style] go-ahead unclear: ask one line before writing anything.")
    else:
        lines.append("[style] discussion, not a go-ahead: answer, then stop.")
    if verdict == "liked":
        lines.append("[style] previous answer LIKED → run skill style:fix to record it as an example.")
    elif verdict == "disliked":
        conf = unit(ans["prev_issue"].get("confidence", 0))
        lines.append(f"[style] previous answer DISLIKED: {issue} ({conf:.2f}) → run skill style:fix before answering.")
    return "\n".join(lines)


def pick(answer: dict, allowed) -> str:
    """The model's choice only if it is one of ours; otherwise the strongest allowed option."""
    choice = answer.get("choice")
    if choice is not None and choice in allowed:
        return choice
    probs = {k: v for k, v in answer.get("probabilities", {}).items() if k in allowed}
    if not probs:
        raise ValueError("no valid choice")
    return argmax(probs)


def argmax(probs: dict) -> str:
    return max(probs, key=lambda key: unit(probs[key]))


def unit(value) -> float:
    """A finite number in [0, 1]; anything else is a broken answer, not a weak one."""
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"out of range: {value}")
    return number


def log(entry: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        rows = LOG.read_text().splitlines() if LOG.exists() else []
        rows.append(json.dumps(entry, ensure_ascii=False))
        LOG.write_text("\n".join(rows[-LOG_KEEP:]) + "\n")
    except OSError:
        pass


def tail(count: int) -> None:
    """One line per recent call: time, the user's words, mode, go-ahead, verdict."""
    rows = LOG.read_text().splitlines()[-count:] if LOG.exists() else []
    for line in rows:
        row = json.loads(line)
        ans = row.get("answers") or {}
        said = row["request"]["state"]["user_message"].replace("\n", " ")[:60]
        head = f'{row.get("ts", "?")}  {row.get("backend", "claude"):<8} {row["ms"]:>5}ms'
        if not ans:
            print(f'{head}  FAILED  «{said}»')
            continue
        verdict = ans["prev_verdict"]["choice"]
        if verdict == "disliked":
            verdict += ":" + ans["prev_issue"]["choice"]
        print(f'{head}  {ans["reply_mode"]["choice"]:<8} '
              f'go={ans["go_ahead"]["noul"]:.2f}  prev={verdict:<18} «{said}»')


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--model", choices=BACKENDS,
                      default=os.environ.get("STYLE_CLASSIFIER_BACKEND") or "claude")
    args.add_argument("--tail", type=int)
    opts = args.parse_args()
    if opts.tail:
        tail(opts.tail)
        sys.exit(0)
    try:
        main(opts.model)
    except Exception:  # a broken classifier must never block the prompt
        pass
