---
name: refactoring-guru
description: Use when refactoring code, improving code quality, cleaning up code, writing production-quality code, or applying coding standards. Provides methodology and reference materials for systematic refactoring.
---

# Refactoring Guru

Methodology-driven refactoring with curated code standards.

## Step 1: Read the Navigation Map

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/refactoring-guru/references/navigation-map.md
```

This shows all available references organized by language and concern.

## Step 2: Identify Language and Scope

From the code being refactored, determine:
- **Language:** Python, Swift, JavaScript (or multiple)
- **Scope:** Full service, specific files, or targeted cleanup

## Step 3: Follow the Methodology

Work through each phase in order. Read relevant references before making changes.

### Phase 1: Tests

**Check:**
- Tests exist for code being refactored
- Coverage >= 80%
- All tests passing

**Action:** Do not proceed until tests are solid. Add tests if needed.

### Phase 2: Architecture

**Check against:** `{language}/architecture/*.md` and `{language}/principles.md`

**Action:** Compare current structure to architecture references. Restructure if patterns don't match (MVVM, hexagonal, layers, etc.).

### Phase 3: Elements

**Check against:**
- `{language}/elements/class_body.md` - Class composition
- `{language}/elements/method_structure.md` or `function_structure.md` - Method/function internals
- `{language}/elements/error_handling.md` - Error patterns
- `{language}/elements/async_patterns.md` - Async/concurrency

**Action:** Go through files, compare to element references. Refactor internals to match patterns.

### Phase 4: Polish

**Check against:**
- `{language}/elements/naming.md` - Naming conventions
- `{language}/elements/logging.md` - Logging patterns (if applicable)

**Action:** Final pass for consistency. Fix naming, logging, and remaining style issues.

## Recommendations

**Sub-agents:** Consider spawning sub-agents for phases 2-4. This keeps context light and enables parallel work.

**Commits:** Commit after each phase to create clear checkpoints.

**Use references:** Read relevant reference files before making changes (e.g., `${CLAUDE_PLUGIN_ROOT}/skills/refactoring-guru/references/swift/elements/naming.md`). If creating a plan, include which references apply to each phase - this is crucial for quality refactoring.

## Quick Reference

| Phase | What to Check | References to Load |
|-------|--------------|-------------------|
| Tests | Coverage, passing | - |
| Architecture | Structure, layers | `architecture/*.md`, `principles.md` |
| Elements | File internals | `elements/class_body.md`, `method_structure.md`, `error_handling.md`, `async_patterns.md` |
| Polish | Naming, logging | `elements/naming.md`, `elements/logging.md` |
