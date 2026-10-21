---
name: drawing-agterm-explainers
description: Use when the session runs inside agterm (AGTERM_ENABLED=1) and the user asks for a diagram, flowchart, scheme, explainer or interactive walkthrough of how something works — a skill, a pipeline, a protocol, a codebase flow — or wants to "see" a process instead of reading it.
---

# Drawing agterm explainers

## Overview

An explainer is an HTML page shown in agterm's right split pane while the conversation goes on in the left one. Steps read top-down, short labels are visible, and depth opens only on click.

Before drawing, read `~/.claude/agterm-visuals/feedback.md` if it exists: it holds this user's corrections from earlier pages and overrides this skill.

## Where it goes

```bash
S=(--target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET")
agtermctl session split on --axis vertical "${S[@]}"            # skip if tree shows split: true
agtermctl session overlay open --html "$F" --js --pane right "${S[@]}"   # always --js: every page carries script
agtermctl session focus left "${S[@]}"                           # keep typing in the chat
agtermctl session overlay reload --pane right "${S[@]}"          # after every rewrite
```

Not a full-session overlay: it covers the chat. The page lives in the scratchpad.

Every page is dynamic: it opens with `--js` and carries the comments layer (below). There is no static variant — the layer costs nothing, and a page without it cannot be commented back to the chat.

## What the page is

1. **Title, one-line subtitle, legend** of who acts (one color per actor).
2. **Flow, top to bottom.** The main path runs straight down the center. Shapes: pill = start/end, box = action, diamond = decision, parallelogram = data or message. Border color = actor. A side branch leaves a diamond to the right with a short labeled arrow (Нет / BLOCKED / FAILED). A loop back is a tag on the node ("↩ новый пакет"), never a long back edge.
3. **Short labels only.** Explanation goes behind a click: `<details>` on a plain flow, the panel below on a walkthrough.
4. **Dashed arrows animated** in the flow direction; the arrow into the active step is highlighted. Respect `prefers-reduced-motion`.

When the process has decisions, make it an **interactive walkthrough**:

- Buttons sit on the decision nodes themselves (Да / Нет, DONE / BLOCKED), plus "Дальше ↓" on plain steps and "↺ Сначала" at the top.
- A **sticky bottom panel** shows what actually travels at the current step: route line (`Opus → pi-runner · Agent prompt`), title, the exact payload, 1–3 notes.
- The panel **collapses to its header** (route + title) on a click on the header or its ▾ button, and expands the same way. The state is remembered per page title in `localStorage` and survives `overlay reload`; a step change never reopens a collapsed panel, and the page's `padding-bottom` shrinks with it (`body.pmin`).
- Drive it with **one concrete running example** (a real-looking task), not placeholders. Loops change the payload (attempt counter, fallback model, v2 packet).
- Structured payloads are **vertical key: value blocks**, YAML-like, one key per line. Every key is clickable and opens a popover saying what it means. No legend list of fields under the block.

`examples/interactive-walkthrough.html` is a complete working page with all of the above (state machine, panel, popovers, shapes); copy its CSS and structure.

## Technical rules

| Rule | Why |
|---|---|
| Colors from `--agterm-foreground`, `--agterm-background`, `--agterm-color-1…6` with fallbacks; never declare `--agterm-*` | Page matches the terminal theme |
| Declare your own aliases (`--bg`, `--opus`…) on `body`, not on an inner wrapper | A fixed panel or popover outside the wrapper loses them and renders transparent |
| Opaque surfaces: `background: linear-gradient(var(--bg), var(--bg)), Canvas` | The agterm background can be translucent |
| Diamond/parallelogram via two `clip-path` layers (`::before` border color, `::after` inset background) | Real shapes with text inside, no SVG layout math |
| A decision row is a `1fr auto 1fr` grid: the diamond in the middle column, the side arrow and node in the right one | A centered flex row centers diamond + branch together and pushes the diamond off the arrows' axis |
| Under 640px the side node drops under the diamond, right-aligned with `↳`; page `padding-bottom` ≥ panel height | The right pane is narrow; the panel must not hide the last node |
| Always open with `--js` | JS is off in agterm overlays by default; the comments layer and any walkthrough need it |

## Comments to chat

Every page lets the user comment on any element and send the notes to the chat. The layer (one `<style id="cm-style">` + one `<script id="cm-script">`, plus the `.cm-link` in the key popover) lives in `examples/interactive-walkthrough.html`: copy both blocks into every page, a plain flow too. Set `CM.sel` to the page's commentable selectors (`.node` plus whatever tables or paragraphs the page has).

- It calls `agterm.request('session.type', {args: {text, pane: 'left'}})`. Outside agterm it shows the text to copy.
- `session.type` sends Return per newline and does not space Returns inside a payload, so the message must be ONE line plus a single trailing `\n`.
- Put `<meta name="explainer-rev" content="N">` in the head and bump it on every rewrite: sent comments stay as history, and leftovers from an older rev are tagged.

## Comments in GitLab

A page shared with agterm's Share (Settings > Sharing with an OAuth Application ID) gets threads from colleagues: on GitLab Pages they sign in and comment blocks; inside agterm the same threads show read-only, with "▶ Следить" polling every 30 s for an hour.

- Paste the two blocks of `examples/gitlab-comments.html` (`<style id="gl-style">`, `<script id="gl-script">`) into every page, after the cm-script. Without Share's metas and outside agterm it does nothing.
- Give every block a colleague may discuss a `data-anchor` with a short readable name that survives rewrites: `data-anchor="строки 16–19"`, `data-anchor="шаг: Opus → pi"`. A thread sticks to that name; renaming a block moves its threads to "без блока".
- Bump `explainer-rev` on a rewrite: a thread left on an older rev is marked as such on its block.

## Before saying it's done

1. `node --check` on the extracted `<script>`.
2. Screenshot and look at it: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=870,1000 --screenshot="$OUT" "file://$F"`, then Read the PNG. Headless capture breaks on a scrolled or smooth-scrolling page: to check a later step of a walkthrough, render a temp copy that starts at that step with `scrollIntoView` removed.
3. `agtermctl tree --json --window "$AGTERM_WINDOW_ID" --socket "$AGTERM_SOCKET" | jq '.. | .htmlOverlays? // empty'` shows `state: loaded`.

## Collecting feedback

When the user corrects anything about a page (layout, readability, interaction, wording), fix it, then append one line to `~/.claude/agterm-visuals/feedback.md`: `- <YYYY-MM-DD>: <what to do instead>`. When that file holds lessons that apply to everyone, propose folding them into this skill.
