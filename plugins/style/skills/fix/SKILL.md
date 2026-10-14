---
name: fix
description: Run when the [style] directive glued to the user's prompt says the previous answer was LIKED or DISLIKED. Keeps ~/.claude/style-examples.md, the few-shot record of how the user wants to be answered, and rewrites a disliked answer in that style before answering. Never load the examples file on an ordinary prompt; this skill is the only reader.
---

# style:fix

The plugin hook `scripts/classify.py` grades every user message. Two of its verdicts land here.

## DISLIKED: `previous answer DISLIKED: <issue> (<confidence>)`

1. Gate first. If the user's message already says what is wrong or supplies the correction, go on.
   If it does not (vague "это фигня, переделывай") and `<confidence>` is below 0.5 or the issue is
   `wrong_facts`, ask one line: what exactly is off. Stop there; rewrite and record only once the
   answer arrives.
2. Read `~/.claude/style-examples.md` (good examples + bad→good pairs).
3. Redo the previous answer the way the examples show. Short wins: fewer lines, plain words,
   one answer, no identifiers unless the user asked for a trace.
4. Append a `## bad → good` pair: the user's original question, 3–5 lines of the disliked answer
   (enough to recognise the pattern), the rewrite. Note the issue label.
5. Then answer the current message, in the same style.

## LIKED: `previous answer LIKED`

1. Append a `## good` example: the user's question and the liked answer, verbatim.
2. Answer the current message. Do not mention the recording.

## File rules

- `~/.claude/style-examples.md`, newest at the bottom. Keep it under ~40 examples; when it grows past that, drop the oldest `good` that duplicates a newer one.
- One example per `##` heading, question first, answer after a blank line, Russian stays Russian.
- Never rewrite old examples to fit a new theory; the file is a record, not a rulebook.
