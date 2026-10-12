#!/bin/bash
# SessionStart hook: report rules and doc edits drafted by reflection that wait for the human.
LESSONS=$HOME/.claude/delegate-to-pi/lessons
shopt -s nullglob
files=("$LESSONS"/proposals/*.md)
[ -f "$LESSONS/rules.pending.md" ] && echo "delegate-to-pi: рефлексия предлагает новые правила: $LESSONS/rules.pending.md (выкинутое и почему: rules.dropped.md). Покажи человеку diff с rules.md и список выкинутого; одобрит — mv rules.pending.md rules.md, отклонит — удали rules.pending.md; в обоих случаях удали rules.dropped.md."
[ ${#files[@]} -gt 0 ] && echo "delegate-to-pi: есть предложения рефлексии: ${files[*]}. Покажи человеку кратко, примени одобренное, файл удали."
exit 0
