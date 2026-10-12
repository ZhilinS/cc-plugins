#!/bin/bash
# SessionEnd hook: compact the session transcript, then let pi draft new lessons in the background.
# Only sessions that spawned pi-runner are reflected. The new rules land in rules.pending.md
# and reach rules.md only after the human approves them (see SKILL.md).
# Modes: reflect.sh [<transcript> <cwd>]   |   reflect.sh --pi <id> <cwd>

DIR=$(cd "$(dirname "$0")" && pwd)
LESSONS=$HOME/.claude/delegate-to-pi/lessons
LOG=$LESSONS/reflect.log
mkdir -p "$LESSONS/work" "$LESSONS/proposals"
touch "$LESSONS/rules.md" "$LESSONS/inbox.md"

if [ "$1" = "--pi" ]; then
  ID=$2
  PROJECT=$3
  W=$LESSONS/work/$ID.txt

  # Sessions often end together; one reflection at a time, or they overwrite each other's rules.
  LOCKED=no
  for _ in $(seq 360); do
    mkdir "$LESSONS/.lock" 2>/dev/null && { LOCKED=yes; break; }
    sleep 5
  done
  if [ "$LOCKED" = no ]; then
    printf '%s %s lock busy for 30 min, skipped\n' "$(date '+%F %T')" "$ID" >>"$LOG"
    exit 0
  fi
  trap 'rmdir "$LESSONS/.lock"' EXIT

  # Build on unapproved rules so pending lessons are not lost between sessions.
  BASE=$LESSONS/rules.md
  [ -f "$LESSONS/rules.pending.md" ] && BASE=$LESSONS/rules.pending.md

  FILES=("@$W" "@$LESSONS/inbox.md" "@$BASE")
  for F in "$PROJECT/AGENTS.md" "$PROJECT/MCP.md"; do
    [ -f "$F" ] && FILES+=("@$F")
  done

  read -r -d '' PROMPT <<'PROMPT_EOF'
You are the reflection step of the delegate-to-pi skill. Claude Code delegates work to the pi CLI (a text-only model). This step learns from one finished session.

Attached files:
- the session's compacted transcript: one event per line (USER:, ASSISTANT:, TOOL <name>:, RESULT:). Subagent events follow the main session after a "--- subagent" line.
- inbox.md: raw lessons appended since the last reflection.
- rules.md: the current consolidated rules.
- AGENTS.md and MCP.md of the project, when attached.

Do two things.

1. RULES: write the complete new rules.md. At most 40 lines, each an imperative one-line rule about delegating work to pi: task packet shape, model choice and fallback, timeouts and empty stdin, prompt shape and length, output format, tool quirks. Merge the current rules, the inbox lines, and lessons visible in the transcript (calls that hung, timed out, returned wrong or empty output, wasted calls, prompt shapes that failed). Drop duplicates and stale rules. Use only facts present in the inputs; invent nothing. Start each line with "- ". No title, no commentary.

2. PROPOSAL: propose edits to the project docs AGENTS.md or MCP.md only when the transcript shows a concrete fact about this project (iOS simulator, iPhone/Xcode MCP bridge, build gotchas) that those docs lack. For each edit give: "File: <AGENTS.md or MCP.md>", "Anchor: <existing heading or line the text goes after>", "Text:" with the exact text to add in the language of the target file, and "Evidence:" one line naming the transcript event. Skip anything already present in those files and any style advice. If nothing qualifies, reply NONE.

Output exactly two sections and nothing else, no markdown code fences:
=== RULES ===
<complete rules.md content>
=== PROPOSAL ===
<NONE, or the edits>
PROMPT_EOF

  OUT=$(perl -e 'alarm 900; exec @ARGV' pi -p --provider opencode-go --model muse-spark-1.3-contributor --no-session "$PROMPT" "${FILES[@]}" </dev/null 2>>"$LOG")
  RC=$?
  if [ "$RC" -ne 0 ] || [ -z "$OUT" ]; then
    printf '%s %s pi rc=%s, nothing written\n' "$(date '+%F %T')" "$ID" "$RC" >>"$LOG"
    exit 0
  fi

  RULES=$(printf '%s\n' "$OUT" | sed -n '/^=== RULES ===$/,/^=== PROPOSAL ===$/p' | sed '1d;$d')
  PROPOSAL=$(printf '%s\n' "$OUT" | sed -n '/^=== PROPOSAL ===$/,$p' | sed '1d')

  if [ -z "$RULES" ]; then
    printf '%s %s no RULES section\n' "$(date '+%F %T')" "$ID" >>"$LOG"
    exit 0
  fi

  printf '%s\n' "$RULES" >"$LESSONS/rules.pending.md"
  : >"$LESSONS/inbox.md"

  PROP=no
  PN=$(printf '%s' "$PROPOSAL" | tr -d '[:space:]')
  if [ -n "$PN" ] && [ "$PN" != "NONE" ]; then
    {
      printf '# Предложения рефлексии\n'
      printf 'Проект: %s\n' "$PROJECT"
      printf 'Сессия: %s\n' "$ID"
      printf '\n%s\n' "$PROPOSAL"
    } >"$LESSONS/proposals/$(date +%F)-${ID:0:8}.md"
    PROP=yes
  fi

  printf '%s %s ok rules=%s proposal=%s\n' "$(date '+%F %T')" "$ID" "$(wc -l <"$LESSONS/rules.pending.md" | tr -d ' ')" "$PROP" >>"$LOG"
  exit 0
fi

if [ $# -ge 2 ]; then
  TRANSCRIPT=$1
  PROJECT=$2
else
  HOOK=$(cat)
  TRANSCRIPT=$(printf '%s' "$HOOK" | jq -r '.transcript_path // empty')
  PROJECT=$(printf '%s' "$HOOK" | jq -r '.cwd // empty')
fi
ID=$(basename "$TRANSCRIPT" .jsonl)

# Nothing to learn from sessions without pi-runner, and their transcripts stay local.
grep -qE '"subagent_type": ?"[^"]*pi-runner"' "$TRANSCRIPT" || exit 0

JQ='
def clean: gsub("[\n\r\t]"; " ") | .[0:300];
def emit($p): clean | select(. != "") | $p + .;
select(.type == "user" or .type == "assistant")
| if .type == "user" then
    if (.message.content | type) == "string" then
      (if .isMeta == true then empty else (.message.content | emit("USER: ")) end)
    else
      .message.content[]? | select(.type == "tool_result")
      | (.content | if type == "string" then . else ([.[]? | select(.type == "text") | .text] | join(" ")) end)
      | emit("RESULT: ")
    end
  else
    .message.content[]?
    | if .type == "text" then (.text | emit("ASSISTANT: "))
      elif .type == "tool_use" then (.name as $n | (.input | tojson) | emit("TOOL " + $n + ": "))
      else empty end
  end
'

TMP=$LESSONS/work/$ID.txt
jq -r "$JQ" "$TRANSCRIPT" >"$TMP"

shopt -s nullglob
for SA in "$(dirname "$TRANSCRIPT")/$ID"/subagents/agent-*.jsonl; do
  AID=$(basename "$SA" .jsonl)
  printf '%s\n' "--- subagent ${AID#agent-} ---" >>"$TMP"
  jq -r "$JQ" "$SA" >>"$TMP"
done

if [ "$(wc -c <"$TMP")" -gt 120000 ]; then
  tail -c 120000 "$TMP" | tail -n +2 >"$TMP.tmp"
  mv "$TMP.tmp" "$TMP"
fi

nohup bash "$DIR/reflect.sh" --pi "$ID" "$PROJECT" </dev/null >>"$LOG" 2>&1 &
disown
exit 0
