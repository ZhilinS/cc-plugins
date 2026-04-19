# Refactoring Guru Plugin

## Layered References

Reference files live in three layers (priority high → low):

1. `$PROJECT_ROOT/.claude/refactoring-guru/references/` — project overrides
2. `$HOME/.claude/refactoring-guru/references/` — user overrides
3. `plugins/refactoring-guru/skills/prepare-refactor/references/` — plugin defaults

Resolution is **directory-replace, per category**: for each logical path, the first layer that contains it owns it fully — contents of the same directory in lower layers are ignored. Resolution happens per category (`principles.md`, `elements/`, `architecture/`), so a project can own `python/elements/` without touching `python/architecture/`.

## Maintenance Rules

- **Adding a new language** — create `references/<language>/` with `principles.md`, `elements/*.md`, and `architecture/*.md`. The exploration agent picks it up automatically via the discovery convention (see `skills/prepare-refactor/SKILL.md` → "Stage 1a"). Same procedure applies at user/project layers.
- **Adding, removing, or renaming files inside an existing language** — no plugin-side wiring needed; the exploration agent enumerates files from the filesystem.
- **Changing discovery rules** (e.g., adding a new `architecture/<pattern>.md` convention) — update the exploration prompt in `skills/prepare-refactor/SKILL.md` (Stage 1a) and mirror the change in `skills/parallel-execution-refactor/SKILL.md` if needed.
