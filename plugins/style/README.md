# Style

A classifier reads every prompt you send and glues a short `[style]` directive to it: the reply mode (short, detailed, trace, code, design), the length limit, whether you asked to start work or are still discussing, and whether you liked or disliked the previous answer. Liked and disliked answers become few-shot examples that Claude follows next time.

## Install

```bash
/plugin marketplace add ZhilinS/cc-plugins
/plugin install style@zhilin-cc-plugins
```

Needs `python3` and the CLI or key of the backend you pick.

## What's inside

- `hooks/hooks.json` — `UserPromptSubmit` runs `scripts/classify.py`. Prompts that start with `/` are skipped.
- `skills/fix` (`style:fix`) — on a LIKED/DISLIKED verdict, records the example and rewrites a disliked answer.
- `commands/log.md` (`/style:log`) — the last 10 verdicts, with backend and latency.

## Backends

The question set and the answer format follow the [TypeSafe.ai System One API](https://docs.typesafe.ai/api). Each backend is a call plus a parser that brings its output back to that `answers` shape.

| Backend | Call | Default model |
|---|---|---|
| `claude` (default) | `claude -p`, isolated from your settings and hooks | `haiku` |
| `opencode` | `opencode run --pure -m <model>` | `opencode-go/deepseek-v4.1-flash` |
| `pi` | `pi -p --no-tools --system-prompt …` | `opencode-go/deepseek-v4.1-flash` |
| `jev` | `POST https://api.typesafe.ai/v1/systemone` | `jev-latest` |

Pick one per machine in `~/.claude/settings.json`:

```json
"env": {
  "STYLE_CLASSIFIER_BACKEND": "opencode",
  "STYLE_CLASSIFIER_MODEL": "opencode-go/deepseek-v4.1-flash",
  "TYPESAFE_API_KEY": "…"
}
```

`STYLE_CLASSIFIER_MODEL` overrides the backend's default model id. `TYPESAFE_API_KEY` is needed only for `jev`. To try a backend by hand:

```bash
echo '{"prompt":"explain how this works","transcript_path":""}' | python3 scripts/classify.py --model opencode
```

A backend that fails or times out (12 s) adds nothing to the prompt; `/style:log` shows it as `FAILED`.

Adding a backend is one `call_<name>` function, a parser (`parse_text` fits any CLI that prints the model text) and a line in `BACKENDS`. Tests: `cd scripts && python3 -m unittest test_classify`.

## Before you install

- **Where data goes.** Your prompt and the previous exchange (up to 6000 characters each) go to the chosen backend on every prompt.
- **Your data.** The examples live in `~/.claude/style-examples.md`, the call log (last 200 calls, full request and answers) in `~/.claude/state/style-classifier/log.jsonl`.
