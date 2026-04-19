# Refactoring Plan: <Scope Description>

> **For Claude:** Use refactoring-guru:parallel-execution to execute this plan.

**Scope:** [files/service being refactored]
**Language:** [python/java]
**Date:** YYYY-MM-DD

---

## Phase 1: Tests

Status: [PASS / NEEDS WORK]
[If NEEDS WORK, list what tests are missing or failing]

## Phase 2: Architecture

### [Rule Name from reference ## heading]
**Reference:** `references/{lang}/architecture/{file}.md`
**Files:** `path/to/file.py:45-60`
**Violation:** [What's wrong]
**Fix:** [What to do]

### [Next Rule Name]
**Reference:** `references/{lang}/architecture/{file}.md`
**Files:** `path/to/other_file.py:10-25`
**Violation:** [What's wrong]
**Fix:** [What to do]

## Phase 3: Re-evaluate

**After architecture fixes are applied, re-run the refactoring-guru:refactor skill on the updated codebase.** Architecture changes have altered the file layout — file paths and line numbers from the original review are no longer valid. A fresh review will produce a new plan with accurate references for Elements and Polish phases.

---

## Summary

| Phase | Violations |
|-------|-----------|
| Architecture | N |
| Elements | deferred — re-evaluate after architecture fixes |
| Polish | deferred — re-evaluate after architecture fixes |
| **Total** | **N (architecture only)** |
