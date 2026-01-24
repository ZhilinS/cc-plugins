# JavaScript ES6+ Refactoring Rules Design

**Date:** 2026-01-24
**Status:** Approved

## Overview

Create framework-agnostic JavaScript ES6+ refactoring rules following the existing pattern established by Python and Swift rules.

## Decisions

- **Framework-agnostic:** Pure ES6+ patterns, framework-specific rules can go in `architecture/` later
- **Core subset first:** 4 files to start, expand based on real needs
- **Functional-leaning:** Pure functions, immutability, composition over classes
- **Pure JavaScript:** No TypeScript (can be separate folder later)

## Structure

```
references/javascript/
├── principles.md              # Core ES6+ style principles
└── elements/
    ├── naming.md              # Naming conventions
    ├── function_structure.md  # Function patterns
    └── async_patterns.md      # Promise/async patterns
```

## principles.md

| Principle | Key Points |
|-----------|------------|
| Const by Default | Use `const` unless rebinding needed. Never `var`. `let` only for loops/reassignment. |
| Pure Functions First | Same input → same output. No side effects. Easier to test and reason about. |
| Immutability Over Mutation | Return new objects/arrays instead of mutating. Use spread `...` for updates. |
| Composition Over Inheritance | Small functions that compose. Factory functions over classes. |
| Explicit Over Magic | No hidden behavior. Clear data flow. Avoid `this` when possible. |
| Early Returns | Guard clauses at top. Flat code over nested conditionals. |

## naming.md

| Rule | Convention |
|------|------------|
| No `is` prefix for adjectives | `active`, `visible`, `enabled` - not `isActive` |
| Verb prefixes for questions | `hasPermission()`, `canEdit()`, `shouldRetry()` |
| Context gives meaning | `fetchBacklinks()` makes `request` and `items` inside perfectly clear |
| Collection plurals | `users` not `userList`, iterate with `user` |
| Keep names short | `user` not `currentUserObject` |
| camelCase variables/functions | `userName`, `fetchData` |
| PascalCase constructors | `UserService`, `HttpClient` |
| SCREAMING_SNAKE constants | `MAX_RETRIES`, `API_URL` |
| Action prefixes | `fetch` (external), `create` (new), `build` (from parts), `parse` (from raw) |

## function_structure.md

| Rule | Guidance |
|------|----------|
| Arrow functions by default | `const fn = (x) => x + 1` - concise, no `this` binding issues |
| Regular functions when needed | Hoisting, recursion by name, generator functions |
| Single responsibility | One function = one job |
| 15-20 lines max | Keep function signature visible on screen |
| Early returns | Guard clauses at top, then happy path |
| Pure over impure | Same input → same output. Side effects at edges. |
| Composition over nesting | Chained calls over deeply nested logic |

## async_patterns.md

| Rule | Guidance |
|------|----------|
| async/await over .then() | More readable, easier to debug |
| Promise.all for parallel | Independent operations run concurrently |
| Promise.allSettled for partial failures | When you want all results even if some fail |
| Error handling at boundaries | Catch at edges, let errors propagate through pure functions |
| Avoid mixing callbacks and promises | Pick one pattern |

## Implementation Tasks

1. Create `references/javascript/` directory structure
2. Write `principles.md`
3. Write `elements/naming.md`
4. Write `elements/function_structure.md`
5. Write `elements/async_patterns.md`
6. Update `navigation-map.md` with JavaScript section
