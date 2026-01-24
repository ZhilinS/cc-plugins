# Swift Language Support for Refactoring-Guru Plugin

## Overview

Add Swift language rules and snippets to the refactoring-guru plugin, targeting iOS/macOS app development with SwiftUI.

## Target Stack

- **Platform:** iOS/macOS app development
- **Architecture:** MVVM
- **UI Framework:** SwiftUI primary with UIKit interop
- **Async/Data flow:** async/await + @Observable (iOS 17+)
- **Dependency Injection:** Protocol-based + SwiftUI Environment

## Directory Structure

```
references/swift/
├── principles.md
├── elements/
│   ├── view_structure.md
│   ├── viewmodel_design.md
│   ├── async_patterns.md
│   ├── error_handling.md
│   ├── naming.md
│   ├── protocols.md
│   └── uikit_interop.md
└── architecture/
    ├── mvvm_swiftui.md
    ├── navigation.md
    └── dependency_injection.md
```

## File Specifications

### principles.md

Six core Swift principles:

1. **Value Types First** - Prefer structs over classes; use classes only for identity, inheritance, or reference semantics
2. **Protocol-Oriented Design** - Define behavior through protocols, not inheritance; use protocol extensions for defaults
3. **Explicit Over Implicit** - Avoid force unwrapping; use guard let for early exits; prefer if let over implicit unwrapping
4. **Composition Over Inheritance** - Build views from small components; ViewModifiers over base classes; protocol composition
5. **Immutability by Default** - Use let unless mutation required; prefer immutable data models; state flows through ViewModels
6. **Fail Fast, Recover Gracefully** - Validate at boundaries; typed errors for recoverable failures; crash on programmer errors

### elements/view_structure.md

SwiftUI view composition patterns:
- Keep views under 50 lines, extract subviews
- Computed properties for conditional content
- ViewBuilders for reusable layouts
- Avoid logic in view body - delegate to ViewModel
- Bad/Good examples for each pattern

### elements/viewmodel_design.md

@Observable ViewModel patterns:
- One ViewModel per screen/feature
- Public read-only state with private(set) for mutations
- Actions as methods, not published vars
- Lifecycle management with `.task` modifier
- Testing strategies

### elements/async_patterns.md

Swift concurrency patterns:
- Structured concurrency with TaskGroups
- Actor for shared mutable state
- MainActor for UI updates
- Cancellation handling with Task.checkCancellation()
- Common pitfalls and solutions

### elements/error_handling.md

Error handling patterns:
- Typed error enums conforming to Error
- Result type for async boundaries
- When to throw vs return optional
- User-facing error presentation
- Error recovery strategies

### elements/naming.md

Swift naming conventions (diverging from Apple where needed):
- **No `is` prefix for boolean adjectives** - `loading` not `isLoading`, `visible` not `isVisible`
- Verb prefixes for boolean methods: `has`, `should`, `can`
- Collection plurals: `users` not `userList`
- Action method prefixes: `fetch_`, `create_`, `build_`, `parse_`
- Full words except universal abbreviations (URL, API, ID)

### elements/protocols.md

Protocol-oriented design and DI:
- Protocol per dependency boundary
- Default implementations via extensions
- Mocking strategies for tests
- Protocol composition patterns
- When to use associated types vs generics

### elements/uikit_interop.md

Bridging SwiftUI and UIKit:
- UIViewRepresentable structure and lifecycle
- Coordinator pattern for delegates
- UIViewControllerRepresentable patterns
- When to drop to UIKit (complex gestures, legacy components)
- Avoiding retain cycles

### architecture/mvvm_swiftui.md

MVVM architecture with SwiftUI:
- Feature module directory structure
- ViewModel lifecycle with `.task` and `.onDisappear`
- State management with @Observable
- View-ViewModel binding patterns
- Testing ViewModels in isolation
- Complete code examples

### architecture/navigation.md

Navigation patterns:
- NavigationStack with path-based routing
- Deep linking support
- Coordinator pattern for complex flows
- Sheet/fullscreen presentation
- Navigation state persistence

### architecture/dependency_injection.md

Dependency injection strategies:
- Protocol definitions at module boundaries
- Environment injection for view-level dependencies
- Initializer injection for ViewModels
- Test doubles and mocking
- Production vs preview configurations

## Updates Required

Update `navigation-map.md`:
- Add Swift to the Structure tree
- Add Swift row to Elements table
- Add Swift row to Architecture table
- Update Quick Reference table with Swift examples

## Implementation Order

1. Create `swift/` directory structure
2. Write `principles.md`
3. Write elements files (7 files)
4. Write architecture files (3 files)
5. Update `navigation-map.md`
