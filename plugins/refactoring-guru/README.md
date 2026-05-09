# Refactoring Guru

Curated coding standards, idioms, and architecture notes for guided refactoring sessions — the kind of stuff a linter can't catch.

## Install

```bash
/plugin marketplace add git@gitlab.semrush.net:ai/agent-marketplace.git
/plugin install refactoring-guru@agent-marketplace
```

## How it runs

Manual only — no hooks, no auto-trigger. The reference set is heavy, so it loads only when you call a skill on purpose.

## Skills

- `/refactoring-guru:prepare-refactor` — the full pass: explore → architecture → elements → plan → apply.
- `/refactoring-guru:parallel-execution-refactor` — fans the plan out to sub-agents once multiple files need work.
- `/refactoring-guru:init-overrides` — scaffolds project/user override trees from the plugin defaults.

## When to call it

Kick off a refactor session with one of the skills above. Good fits:

- "Tidy up this module."
- "Bring this service in line with our standards."
- "Check this against our architecture rules."

Skip it for everyday edits — the context cost isn't worth it.

## References

Defaults live in `skills/prepare-refactor/references/`. You can override them per project or per user.

### Layers (highest wins)

1. `$PROJECT_ROOT/.claude/refactoring-guru/references/`
2. `$HOME/.claude/refactoring-guru/references/`
3. plugin defaults

Each layer holds:

- `<language>/{principles.md, elements/*.md, architecture/*.md}` — e.g. `python/`, `java/`, `swift/`
- `common/{principles.md, elements/*.md, architecture/*.md}` — language-agnostic rules

**Resolution is directory-replace per category.** The first layer that has, say, `python/elements/` owns it completely; lower layers are ignored for that directory. Other categories are resolved independently, so a project can override `python/elements/` without touching `python/architecture/` or `common/`.

No pattern detection — every file in the winning `elements/` and `architecture/` directories is loaded. Don't want a rule? Override or delete the file at your layer.

## Maintenance

- **New language** — add `references/<language>/` with `principles.md` plus `elements/` and `architecture/` files. It's picked up automatically.
- **Cross-language rules** — put them under `references/common/`. Loaded on every run alongside the language tree.
- **Add/remove/rename files** — no wiring needed; the filesystem is the source of truth.
- **No cross-references between reference files.** The architecture agent already sees every `architecture/*` and `principles.md` (language + common) in one prompt; links between them just add noise and break when a layer overrides one side.
