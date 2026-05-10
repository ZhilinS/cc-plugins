---
name: init-overrides
description: Use when setting up project- or user-level overrides for refactoring-guru references. Interactively scaffolds the layered directory structure (language overrides + optional common-tree handling) with four modes per category — inherit from a lower layer, keep plugin defaults, customize a working copy, or disable the category entirely.
---

# Init Refactoring Overrides

Interactive scaffolder for the refactoring-guru layered references system. Creates an override tree at the project or user layer so the team can customize language rules, elements, and architecture guidance for their codebase — or opt out of categories that don't fit.

## Why this exists

Refactoring-guru resolves references with **directory-replace per category** (see plugin `CLAUDE.md`). The first layer that contains e.g. `python/elements/` owns it **fully** — files at lower layers in that same directory are ignored.

This single resolution rule has to serve four distinct user intents:

1. **Inherit from a lower layer** — when initializing at the **project** layer, the user already has overrides at the **user** layer for this category and wants those to apply to this project too. Do **not** create anything at the project layer for this category — directory-replace will then fall through to the user layer. Creating even an empty `.gitkeep` here would silently shadow the user-layer overrides. This intent is only meaningful for project-layer init when user-layer overrides exist for the same `(tree, category)`.
2. **Keep plugin defaults** — the user is happy with what the plugin ships. No override needed.
3. **Customize** — the user wants to edit the rules. Override directory is seeded by copying an existing baseline (user-layer overrides if available, otherwise plugin defaults) so the user edits a working copy instead of starting from zero.
4. **Disable** — the user wants to opt out of the category entirely (e.g. `common/architecture/hexagonal_ddd.md` does not fit a Swift app). Override directory is created **empty** (just `.gitkeep`); directory-replace then resolves the category to zero rules.

This skill asks for the intent per category and acts accordingly. Conflating intents — for example, asking a yes/no question that mixes Customize and Disable, or blindly creating an empty tree that shadows user-layer overrides — is a footgun.

## Inputs (ask interactively)

Use `AskUserQuestion` for each step. Do not assume answers.

### 1. Location

Where should the overrides live?

- **Project** — `$PROJECT_ROOT/.claude/refactoring-guru/references/` (shared with the team via git)
- **User** — `$HOME/.claude/refactoring-guru/references/` (personal, applies to every project)

Resolve `$PROJECT_ROOT` from the current working directory's git root. If not in a git repo and the user picked "Project", confirm before proceeding.

### 1a. Scan lower layers (project init only)

If location = **Project**, scan `$HOME/.claude/refactoring-guru/references/` and record, for each `(tree, category)` pair, what is already present at the user layer:

- **customize** — directory exists and contains real files (not just `.gitkeep`).
- **disable** — directory exists and contains only `.gitkeep`.
- **absent** — directory does not exist (plugin defaults still apply at the user layer).

Print a short summary of what user-layer overrides exist before asking further questions, so the user understands what the project layer will be layered on top of. This summary drives the per-category defaults in step 4.

If location = **User**, skip this step — there is no lower override layer to inherit from.

### 2. Languages to override

List the languages present in the plugin defaults at `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/` (currently `java`, `python`) plus an explicit "Add a new language" option. Allow multi-select.

For each chosen existing language, proceed to step 4 (per-category mode). For a new language (e.g. `swift`, `typescript`), ask for the language name and then proceed to step 4 as well — do **not** create an empty tree blindly.

Rationale: at the project layer, the user-layer may already define `swift/` (this is exactly the scenario the user-layer scan in step 1a surfaces). Creating `swift/elements/.gitkeep` and `swift/architecture/.gitkeep` at the project layer would shadow those user-layer overrides via directory-replace. Instead, route through the per-category question so each category can be inherited, customized, or disabled explicitly.

For a new language at the **user** layer (no lower layer to inherit from), the per-category options collapse to Customize (start from plugin defaults if any, otherwise an empty placeholder the user will write from scratch) or Disable.

### 3. Common (cross-language) tree

Ask whether to handle the `common/` tree, then proceed to step 4 with `common` as one of the trees. The `common/` tree is loaded **alongside** the language tree on every review, regardless of detected language — so its categories often need explicit `disable` for projects where they don't fit (e.g. backend-flavored architecture rules in a mobile app).

### 4. Per-category mode (for each tree × category)

**Only ask when there is a conflict to resolve.** A category needs the question if and only if some lower layer has actual content that the new override would shadow — i.e. user-layer (when initializing at project) or plugin defaults are non-empty for this `(tree, category)`. If no lower layer has content for this category (e.g. new language `swift`, user-layer empty, no plugin defaults for swift), the per-category question is **skipped** — the category trivially resolves to nothing already, so there is nothing to override. Step 4a below covers the "I want to write rules from scratch anyway" case for those skipped categories.

For each remaining `(tree, category)` pair where `tree ∈ { selected existing or new languages, common }` and `category ∈ { principles, elements, architecture }`, ask **one question with up to four options**. The question header must state the current effective resolution so the user understands what they are about to override:

> `swift/architecture/` currently resolves at: **user layer** (`~/.claude/refactoring-guru/references/swift/architecture/` — 4 files). What do you want at the project layer?

> `python/elements/` currently resolves at: **plugin defaults** (`${CLAUDE_PLUGIN_ROOT}/.../python/elements/` — 6 files). What do you want at the user layer?

The four options:

- **Inherit** — do nothing at this layer. Resolution falls through to the user layer (or plugin defaults if the user layer is also absent for this category). Offered **only** when initializing at the project layer **and** the user layer has a non-absent state for this `(tree, category)`. When offered, it is the default.
- **Keep** — do nothing. Plugin defaults continue to resolve for this category. Always offered when plugin defaults exist for this `(tree, category)`. Default when Inherit is not applicable.
- **Customize** — copy a baseline for this category into the override layer. The user edits a working copy. Baseline source:
  - At the **project** layer, if user-layer overrides exist for this `(tree, category)` and are non-empty, ask whether to seed from the user-layer copy or from the plugin defaults. Prefer user-layer when the user wants to extend their existing rules; prefer plugin defaults when the user wants a fresh start.
  - Otherwise, copy from the plugin defaults.
- **Disable** — create the category directory at this layer with only `.gitkeep` inside. Directory-replace makes the category resolve to zero rules at this layer and below, opting out of this category for every review.

Group the questions by tree to keep the flow tidy: ask all conflicting categories for `python`, then all conflicting categories for `common`, etc. Skip categories the user already declined to override at the tree level.

**Default selection rules:**
- If Inherit is offered → Inherit is the default. Project init should not silently shadow the user layer; the user must explicitly choose to override.
- Otherwise → Keep is the default. The skill should not push users toward customizing or disabling unless they explicitly choose so.

### 4a. Optional fresh-start placeholders

For categories that step 4 skipped because no lower layer had content (typically: a brand-new language with no user-layer setup), offer **one** consolidated yes/no question per tree: "No lower layer has content for `swift/principles`, `swift/elements`, `swift/architecture`. Create empty placeholders here so you can write rules from scratch?" If yes, create `principles.md` (empty) and `elements/.gitkeep`, `architecture/.gitkeep`. If no, create nothing — the user can come back to this skill later. Do **not** ask Inherit/Keep/Customize/Disable for these categories; there is no conflict to resolve.

## Execution

1. Resolve target root (project or user).
2. Locate plugin defaults at `${CLAUDE_PLUGIN_ROOT}/skills/prepare-refactor/references/`. If `CLAUDE_PLUGIN_ROOT` is not set, fall back to scanning known plugin install locations and abort with a clear message if defaults are not found.
3. If target is project, scan `$HOME/.claude/refactoring-guru/references/` to determine the user-layer state per `(tree, category)` (see step 1a). Determine, per `(tree, category)`, whether any lower layer has content — this drives which questions are asked in step 4 vs. handled by step 4a.
4. For each `(tree, category)` × chosen mode:
   - **Inherit** — do nothing. Do not create any directory at the override layer for this category. Verify the chosen target does not already contain anything for this `(tree, category)` from a previous run; if it does, warn the user — leftover files at this layer will continue to shadow the lower layer until removed.
   - **Keep** — do nothing. Do not create any directory at the override layer for this category.
   - **Customize** — copy the chosen baseline (user-layer overrides or plugin defaults, per step 4) for that category from source to target with `cp -R`. If the target already exists and is non-empty, ask before overwriting (skip / overwrite — prefer skip; do not "merge").
   - **Disable** — `mkdir -p <target>/<tree>/<category>` and `touch <target>/<tree>/<category>/.gitkeep`. Do **not** copy any files. If the target already exists and is non-empty, ask before clearing it (skip / clear-and-disable — prefer skip).
5. Print a per-category summary table that names the resolved layer for each category, e.g.:
   - `swift/elements/         → inherited (resolves at user layer: <path>)`
   - `swift/architecture/     → customized (copy at <path>, seeded from user layer)`
   - `python/elements/        → kept (plugin defaults apply)`
   - `python/architecture/    → customized (copy at <path>, seeded from plugin defaults)`
   - `common/architecture/    → disabled (empty override at <path>)`
   And a one-line reminder: *"To revert any decision later: delete the override directory at this layer to fall through to the next layer; replace its contents to switch between customize and disable."*

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
