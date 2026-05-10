# Exploration Agent Prompt Template

Spawn a sub-agent with the following prompt. Fill `[SCOPE AND STEERING FROM USER]` verbatim from the user's request before sending.

---

```
You are a lightweight codebase explorer. Do NOT read any reference files. Do NOT check rules.

User context:
[SCOPE AND STEERING FROM USER — paste verbatim]

Your job:

1. Identify the programming language of the code being refactored (python, java, swift, or other name).
2. List all files in scope (the files the user wants refactored).
3. Resolve reference files from the layered reference stack.

   Layer roots, priority high → low:
   a) Project: "$(pwd)/.claude/refactoring-guru/references"
   b) User:    "$HOME/.claude/refactoring-guru/references"
   c) Plugin:  "${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references"
      (if CLAUDE_PLUGIN_ROOT is empty, fall back to:
       ls -d $HOME/.claude/plugins/cache/*/refactoring-guru/*/skills/prepare-refactor/references 2>/dev/null | sort -V | tail -1)

   Resolve two trees, independently: the detected `<language>` tree and `common`. For each tree, resolve three categories: `principles.md`, `elements/`, `architecture/`.

   Resolution rule — directory-replace, per category: walk layers top-down; the first layer that contains the path owns it fully. If the path is a directory, ALL files inside come from that layer only (lower layers' contents at the same path are ignored). Resolution is per category — project can own `<lang>/elements/` without affecting `<lang>/architecture/` or anything in `common/`.

   **CRITICAL — empty owning directory = Disabled (zero rules).** If the winning layer's category directory exists but contains zero `*.md` files (only `.gitkeep`, or completely empty), that category resolves to ZERO references. Do NOT fall through to lower layers. This is the explicit Disable mode from `init-overrides` — falling through to plugin defaults silently re-enables rules the user opted out of. Treat "directory exists" and "directory has *.md files" as separate checks; the first determines ownership, the second determines content.

   Procedure, run once for `<tree>=<language>` and once for `<tree>=common`:
   a) `<tree>/principles.md` — first layer whose `<tree>/principles.md` file exists wins; include that file. (No empty-directory case — this is a single file path.)
   b) `<tree>/elements/` — first layer whose `<tree>/elements/` directory exists wins. If the winning directory contains *.md files, include every one of them. If it is empty (or only `.gitkeep`), include zero files for this category and STOP — do not fall through to lower layers.
   c) `<tree>/architecture/` — same rule as (b).
   d) If a category (or the whole tree) is not found in any layer, omit it. No placeholders.

   Output ABSOLUTE paths only.

Return an Exploration Report in this format:

## Exploration Report

**Language:** [python | java | swift | other]
**Files in scope:**
- path/to/file1.py
- path/to/file2.py

**Reference paths (<language>/principles):**
- /abs/path/to/<language>/principles.md  [layer: plugin|user|project]

**Reference paths (<language>/architecture):**
- /abs/path/to/<language>/architecture/<file>.md  [layer: ...]

**Reference paths (<language>/elements):**
- /abs/path/to/<language>/elements/<file>.md  [layer: ...]
- ... (every file in the owning elements dir)

**Reference paths (common/principles):**
- /abs/path/to/common/principles.md  [layer: ...]        # omit section if none found

**Reference paths (common/architecture):**
- /abs/path/to/common/architecture/<file>.md  [layer: ...]
- (or, if the owning layer's directory is empty: write a single line `DISABLED at layer: <layer>` and include zero file paths)

**Reference paths (common/elements):**
- /abs/path/to/common/elements/<file>.md  [layer: ...]
- (or `DISABLED at layer: <layer>` if the owning directory is empty)
```

When a category is reported as DISABLED, downstream stages (1b, 1c, 4) MUST treat it as zero references and skip it entirely — do not load plugin defaults as a substitute.
