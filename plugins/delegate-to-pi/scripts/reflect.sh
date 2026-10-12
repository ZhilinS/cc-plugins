#!/bin/bash
# SessionEnd hook: compact the session transcript, then let Claude Opus draft new lessons in the background.
# Only sessions that spawned pi-runner are reflected. The new rules land in rules.pending.md
# and reach rules.md only after the human approves them (see SKILL.md).
# Modes: reflect.sh [<transcript> <cwd>]   |   reflect.sh --run <id> <cwd>

DIR=$(cd "$(dirname "$0")" && pwd)
LESSONS=$HOME/.claude/delegate-to-pi/lessons
LOG=$LESSONS/reflect.log
mkdir -p "$LESSONS/work" "$LESSONS/proposals"
touch "$LESSONS/rules.md" "$LESSONS/inbox.md"

if [ "$1" = "--run" ]; then
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

  FILES=("$W" "$LESSONS/inbox.md" "$BASE")
  for F in "$PROJECT/AGENTS.md" "$PROJECT/MCP.md"; do
    [ -f "$F" ] && FILES+=("$F")
  done

  # Isolated headless run: no user/project settings (so no hooks or plugins, no recursion), no tools, no saved session.
  OUT=$(for F in "${FILES[@]}"; do printf '##### FILE: %s\n' "$(basename "$F")"; cat "$F"; echo; done |
    perl -e 'alarm 900; exec @ARGV' claude -p --model opus --setting-sources "" --tools "" --no-session-persistence \
      --system-prompt-file "$DIR/reflect-prompt.md" "Reflect on the input." 2>>"$LOG")
  RC=$?
  if [ "$RC" -ne 0 ] || [ -z "$OUT" ]; then
    printf '%s %s claude rc=%s, nothing written\n' "$(date '+%F %T')" "$ID" "$RC" >>"$LOG"
    exit 0
  fi

  RULES=$(printf '%s\n' "$OUT" | sed -n '/^=== RULES ===$/,/^=== DROPPED ===$/p' | sed '1d;$d')
  DROPPED=$(printf '%s\n' "$OUT" | sed -n '/^=== DROPPED ===$/,/^=== PROPOSAL ===$/p' | sed '1d;$d')
  PROPOSAL=$(printf '%s\n' "$OUT" | sed -n '/^=== PROPOSAL ===$/,$p' | sed '1d')

  if [ -z "$RULES" ]; then
    printf '%s %s no RULES section\n' "$(date '+%F %T')" "$ID" >>"$LOG"
    exit 0
  fi

  printf '%s\n' "$RULES" >"$LESSONS/rules.pending.md"
  printf '## %s %s\n%s\n\n' "$(date +%F)" "$ID" "$DROPPED" >>"$LESSONS/rules.dropped.md"
  : >"$LESSONS/inbox.md"

  PROP=no
  PN=$(printf '%s' "$PROPOSAL" | tr -d '[:space:]')
  if [ -n "$PN" ] && [ "$PN" != "NONE" ]; then
    {
      printf '# Предложения рефлексии\n'
      printf 'Сессия в проекте: %s\n' "$PROJECT"
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

nohup bash "$DIR/reflect.sh" --run "$ID" "$PROJECT" </dev/null >>"$LOG" 2>&1 &
disown
exit 0
