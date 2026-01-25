# Refactoring Guru Skill Redesign

## Summary

Rename `refactoring-guide` skill to `refactoring-guru` for consistency with plugin name. Transform from a simple reference pointer into a methodology-driven knowledge companion that provides phases, references, and recommendations.

## Goals

1. Provide a refactoring methodology (phases to check)
2. Map references to each phase
3. Recommend sub-agent strategy for context optimization
4. Leave execution decisions to the agent

## Non-Goals

- Prescribing exact tasks or commits (agent's domain)
- Mandating sub-agent spawning (recommendation only)
- Executing code changes (read-only skill)

## Design

### Skill Purpose

Knowledge companion that surfaces code standards during refactoring. Provides methodology (what to check, in what order) and references (how to check it).

### Phases

| Phase | Check | References |
|-------|-------|------------|
| 1. Tests | Tests exist, coverage >= 80%, all passing | - |
| 2. Architecture | Structure matches patterns | `architecture/*.md` |
| 3. Elements | File internals match standards | `elements/class_body.md`, `method_structure.md`, `error_handling.md`, `async_patterns.md` |
| 4. Polish | Naming and logging consistency | `elements/naming.md`, `elements/logging.md` |

### Key Behaviors

- **Language detection:** Agent's responsibility, skill provides navigation map
- **Lazy loading:** References listed, agent reads as needed
- **Non-blocking:** Skill outputs methodology quickly, agent continues
- **Recommendations:** Suggest sub-agents + commits, don't mandate

### Output Format

```markdown
## Refactoring Methodology

### Phase 1: Tests
Check: tests exist, coverage >= 80%, all passing
Do not proceed until tests are solid

### Phase 2: Architecture
Check against: architecture/{detected}/...
Restructure if needed

### Phase 3: Elements
Check against: elements/class_body.md, method_structure.md, error_handling.md, async_patterns.md
Refactor file internals

### Phase 4: Polish
Check against: elements/naming.md, elements/logging.md
Final consistency pass

---

**Recommendation:** Consider spawning sub-agents with relevant references loaded.
This keeps context light and enables parallel work.

Commit after each phase.
```

## Changes Required

1. Rename skill directory: `refactoring-guide` -> `refactoring-guru`
2. Update SKILL.md frontmatter: `name: refactoring-guru`
3. Rewrite SKILL.md content with methodology + phases + recommendations
4. Update any cross-references in plugin

## Context Optimization Strategy (Recommended)

When agent uses sub-agents:
- Main agent orchestrates phases, stays light
- Sub-agents get narrow scope: specific files + specific refs
- Refs passed TO sub-agents in task description
- Enables parallel work in phases 3-4
