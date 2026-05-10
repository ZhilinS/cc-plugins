---
name: init-overrides
description: Use when setting up project- or user-level overrides for refactoring-guru references. Interactively scaffolds the layered directory structure (language overrides + optional common-tree handling) with three modes per category — keep plugin defaults, customize a working copy, or disable the category entirely.
---

# Init Refactoring Overrides

Interactive scaffolder for the refactoring-guru layered references system. Creates an override tree at the project or user layer so the team can customize language rules, elements, and architecture guidance for their codebase — or opt out of categories that don't fit.

## Why this exists

Refactoring-guru resolves references with **directory-replace per category** (see plugin `CLAUDE.md`). The first layer that contains e.g. `python/elements/` owns it **fully** — files at lower layers in that same directory are ignored.

This single resolution rule has to serve three distinct user intents:

1. **Keep plugin defaults** — the user is happy with what the plugin ships. No override needed.
2. **Customize** — the user wants to edit the rules. Override directory is seeded by copying the plugin defaults so the user edits a working copy instead of starting from zero.
3. **Disable** — the user wants to opt out of the category entirely (e.g. `common/architecture/hexagonal_ddd.md` does not fit a Swift app). Override directory is created **empty** (just `.gitkeep`); directory-replace then resolves the category to zero rules.

This skill asks for the intent per category and acts accordingly. A bare yes/no question conflates intents 2 and 3 — that is a footgun.

## Inputs (ask interactively)

Use `AskUserQuestion` for each step. Do not assume answers.

### 1. Location

Where should the overrides live?

- **Project** — `$PROJECT_ROOT/.claude/refactoring-guru/references/` (shared with the team via git)
- **User** — `$HOME/.claude/refactoring-guru/references/` (personal, applies to every project)

Resolve `$PROJECT_ROOT` from the current working directory's git root. If not in a git repo and the user picked "Project", confirm before proceeding.

### 2. Languages to override

List the languages present in the plugin defaults at `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/` (currently `java`, `python`) plus an explicit "Add a new language" option. Allow multi-select.

For each chosen existing language, proceed to step 4 (per-category mode). For a new language (e.g. `swift`, `typescript`), ask for the language name and create an empty tree:

```
<lang>/principles.md          # empty placeholder
<lang>/elements/.gitkeep
<lang>/architecture/.gitkeep
```

A new language has no plugin defaults to seed from, so the per-category question does not apply — the user will write rules from scratch by editing the placeholders.

### 3. Common (cross-language) tree

Ask whether to handle the `common/` tree, then proceed to step 4 with `common` as one of the trees. The `common/` tree is loaded **alongside** the language tree on every review, regardless of detected language — so its categories often need explicit `disable` for projects where they don't fit (e.g. backend-flavored architecture rules in a mobile app).

### 4. Per-category mode (for each tree × category)

For each `(tree, category)` pair where `tree ∈ { selected existing languages, common }` and `category ∈ { principles, elements, architecture }`, ask **one question with three options**:

- **Keep** — do nothing. Plugin defaults continue to resolve for this category. This is the default.
- **Customize** — copy the plugin defaults for this category into the override layer. The user edits a working copy.
- **Disable** — create the category directory at the override layer with only `.gitkeep` inside. Directory-replace makes the category resolve to zero rules, opting out of this category for every review.

Group the questions by tree to keep the flow tidy: ask all three categories for `python`, then all three for `common`, etc. Skip categories the user already declined to override at the tree level.

**Default for all categories: Keep.** The skill should not push users toward customizing or disabling unless they explicitly choose so.

## Execution

1. Resolve target root (project or user).
2. Locate plugin defaults at `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/`. If `CLAUDE_PLUGIN_ROOT` is not set, fall back to scanning known plugin install locations and abort with a clear message if defaults are not found.
3. For each `(tree, category)` × chosen mode:
   - **Keep** — do nothing. Do not create any directory at the override layer for this category.
   - **Customize** — copy the plugin defaults for that category from source to target with `cp -R`. If the target already exists and is non-empty, ask before overwriting (skip / overwrite — prefer skip; do not "merge").
   - **Disable** — `mkdir -p <target>/<tree>/<category>` and `touch <target>/<tree>/<category>/.gitkeep`. Do **not** copy any files. If the target already exists and is non-empty, ask before clearing it (skip / clear-and-disable — prefer skip).
4. For new languages, create the empty tree described in step 2.
5. Print a per-category summary table:
   - `python/elements/        → kept (plugin defaults apply)`
   - `python/architecture/    → customized (copy at <path>)`
   - `common/architecture/    → disabled (empty override at <path>)`
   And a one-line reminder: *"To revert any decision later: delete the override directory to restore plugin defaults; replace its contents to switch between customize and disable."*

## Conventions

- Use `Bash` with `cp -R` for copying. Do not use `Write` to recreate file contents — copy preserves the originals byte-for-byte and lets future plugin updates be diffed cleanly.
- For **disable** mode, create the directory and a single `.gitkeep` file. Never put any other content there — the empty directory is the whole point.
- Never copy from one user's overrides to another layer. Sources are always plugin defaults.
- Do not modify `marketplace.json`, `plugin.json`, or any plugin metadata. This skill only creates files under the chosen `references/` root.
- If the user picked "Project" but `.gitignore` excludes `.claude/`, warn them the overrides will not be shared with the team.

## Out of scope

- Editing reference contents — that's the user's job after scaffolding.
- Detecting which languages a project actually uses — keep selection explicit.
- Migrating between layers (e.g. promoting user overrides to project) — separate concern.
