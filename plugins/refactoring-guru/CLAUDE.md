# Refactoring Guru Plugin

## Layered References

Reference files live in three layers (priority high → low):

1. `$PROJECT_ROOT/.claude/refactoring-guru/references/` — project overrides
2. `$HOME/.claude/refactoring-guru/references/` — user overrides
3. `plugins/refactoring-guru/skills/prepare-refactor/references/` — plugin defaults

Each layer has two kinds of trees, with the same sub-layout:

- `<language>/{principles.md, elements/*.md, architecture/*.md}` — e.g. `python/`, `java/`, `swift/`
- `common/{principles.md, elements/*.md, architecture/*.md}` — language-agnostic rules (shared hexagonal DDD lives here)

Resolution is **directory-replace, per category**: for each logical path (e.g. `python/elements/`, `common/architecture/`), the first layer that contains it owns it fully — contents of the same directory in lower layers are ignored. Resolution happens per category, so a project can own `python/elements/` without touching `python/architecture/` or `common/`.

The exploration agent does not detect architecture patterns. Every file in the winning layer's `elements/` and `architecture/` is included. If certain rules shouldn't apply to a project, remove or override those files at the user/project layer.

## Maintenance Rules

- **Adding a new language** — create `references/<language>/` with `principles.md`, `elements/*.md`, and `architecture/*.md`. The exploration agent picks it up automatically (see `skills/prepare-refactor/SKILL.md` → "Stage 1a"). Same procedure at user/project layers.
- **Adding cross-language rules** — drop them under `references/common/{principles.md, elements/*.md, architecture/*.md}`. They are loaded alongside the language tree for every invocation.
- **Adding, removing, or renaming files** — no plugin-side wiring needed; the exploration agent enumerates files from the filesystem.
- **Don't cross-reference other reference files from inside a reference body.** The Architecture Agent already receives every `architecture/*` + `principles.md` path (language + common) in one prompt; pointers between files add noise and break if a layer overrides one side.
