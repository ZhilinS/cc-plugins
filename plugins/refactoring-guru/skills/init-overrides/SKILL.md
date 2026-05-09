---
name: init-overrides
description: Use when setting up project- or user-level overrides for refactoring-guru references. Interactively scaffolds the layered directory structure (language overrides + optional common/architecture overrides) by copying plugin defaults so they can be customized.
---

# Init Refactoring Overrides

Interactive scaffolder for the refactoring-guru layered references system. Creates an override tree at the project or user layer so the team can customize language rules, elements, and architecture guidance for their codebase.

## Why this exists

Refactoring-guru resolves references with **directory-replace per category** (see plugin `CLAUDE.md`). The first layer that contains e.g. `python/elements/` owns it **fully** — files at lower layers in that same directory are ignored.

That means a hand-rolled override created as an empty directory will silently delete the plugin's defaults for that category. This skill always seeds an override directory with the plugin defaults as a starting point, so the user edits a working copy instead of starting from zero.

## Inputs (ask interactively)

Use `AskUserQuestion` for each step. Do not assume answers.

### 1. Location

Where should the overrides live?

- **Project** — `$PROJECT_ROOT/.claude/refactoring-guru/references/` (shared with the team via git)
- **User** — `$HOME/.claude/refactoring-guru/references/` (personal, applies to every project)

Resolve `$PROJECT_ROOT` from the current working directory's git root. If not in a git repo and the user picked "Project", confirm before proceeding.

### 2. Languages to override

List the languages present in the plugin defaults at `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/` (currently `java`, `python`) plus an explicit "Add a new language" option. Allow multi-select.

For each chosen existing language, the skill seeds the override directory by copying the plugin defaults.

For a new language (e.g. `swift`, `typescript`), create the directory tree with empty placeholder files:

```
<lang>/principles.md
<lang>/elements/.gitkeep
<lang>/architecture/.gitkeep
```

Ask for the language name.

### 3. Common (cross-language) overrides

Ask: override the `common/` tree too (architecture rules shared across languages)?

- **Yes** — copy `common/` from plugin defaults to the chosen layer.
- **No** — skip; plugin defaults continue to apply.

### 4. Per-category granularity (only when overriding existing language/common)

For each tree being overridden, ask which categories to seed:

- `principles.md`
- `elements/`
- `architecture/`

Default: all three. Skipping a category means that category continues to resolve from the plugin defaults (because directory-replace is per category).

## Execution

1. Resolve target root (project or user).
2. Locate plugin defaults at `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/`. If `CLAUDE_PLUGIN_ROOT` is not set, fall back to scanning known plugin install locations and abort with a clear message if defaults are not found.
3. For each `<lang>` × `<category>` selected:
   - If target already exists and is non-empty, ask before overwriting (skip / overwrite / merge — prefer skip).
   - Otherwise, copy recursively from plugin defaults to target.
4. For new languages, create the empty tree described above.
5. Print a summary of created paths and a one-line reminder: *"Edit these files to customize. Removing a category directory restores the plugin defaults for that category."*

## Conventions

- Use `Bash` with `cp -R` for copying. Do not use `Write` to recreate file contents — copy preserves the originals byte-for-byte and lets future plugin updates be diffed cleanly.
- Never copy from one user's overrides to another layer. Sources are always plugin defaults.
- Do not modify `marketplace.json`, `plugin.json`, or any plugin metadata. This skill only creates files under the chosen `references/` root.
- If the user picked "Project" but `.gitignore` excludes `.claude/`, warn them the overrides will not be shared with the team.

## Out of scope

- Editing reference contents — that's the user's job after scaffolding.
- Detecting which languages a project actually uses — keep selection explicit.
- Migrating between layers (e.g. promoting user overrides to project) — separate concern.
