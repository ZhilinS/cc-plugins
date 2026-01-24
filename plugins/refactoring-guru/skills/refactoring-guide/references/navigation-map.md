# Code Samples Navigation Map

Read this file first to understand what's available. Then read only the files relevant to your refactoring task.

## Structure

```
references/
├── navigation-map.md          ← You are here
├── python/
│   ├── principles.md          # High-level style principles
│   ├── elements/              # Code element patterns
│   │   ├── method_signature.md
│   │   ├── method_structure.md
│   │   ├── error_handling.md
│   │   ├── async_patterns.md
│   │   ├── class_body.md
│   │   ├── naming.md
│   │   └── logging.md
│   └── architecture/          # Service architecture patterns
│       ├── hexagonal_ddd.md
│       ├── fastapi_web.md
│       └── grpc_proxy.md
└── swift/
    ├── principles.md          # SwiftUI & iOS 17+ principles
    ├── elements/              # Code element patterns
    │   ├── view_structure.md
    │   ├── viewmodel_design.md
    │   ├── async_patterns.md
    │   ├── error_handling.md
    │   ├── naming.md
    │   ├── protocols.md
    │   └── uikit_interop.md
    └── architecture/          # App architecture patterns
```

## File Descriptions

### Principles (`principles.md`)

High-level style principles that apply broadly:
- Prefer decorators for cross-cutting concerns
- Prefer loose coupling (dependency injection)
- Prefer composition over inheritance
- Prefer lazy initialization
- Prefer explicit over implicit

**Read when:** Starting any refactoring to understand overall philosophy.

### Elements

Code-level patterns for specific constructs:

| File | Content | Read when... |
|------|---------|--------------|
| `method_signature.md` | Type hints, Literal/Enum, kwargs, naming patterns | Refactoring function/method signatures |
| `method_structure.md` | Single responsibility, method length, extraction, composition | Splitting/refactoring method bodies |
| `error_handling.md` | Decorator-based error handling, gRPC/HTTP patterns | Touching try/except, error flows |
| `async_patterns.md` | Async comprehensions, gather, semaphores, timeouts | Working with async/await code |
| `class_body.md` | Private attributes, DI, method organization, dataclasses | Restructuring classes |
| `naming.md` | Context-driven names, conventions, method prefixes | Renaming variables/methods/classes |
| `logging.md` | Event-based logging, structured context, log levels | Adding/refactoring log statements |

### Swift Elements

SwiftUI and iOS 17+ patterns using `@Observable` macro:

| File | Content | Read when... |
|------|---------|--------------|
| `view_structure.md` | View composition, computed properties, @ViewBuilder, subview extraction | Structuring SwiftUI views |
| `viewmodel_design.md` | @Observable ViewModels, private(set), actions as methods, .task lifecycle, ViewState enum, DI | Designing ViewModels |
| `async_patterns.md` | async let, TaskGroup, actors, @MainActor, cancellation, AsyncSequence, timeouts | Working with Swift Concurrency |
| `error_handling.md` | Typed error enums, LocalizedError, Result type, throw vs optional, guard, do-catch specificity | Error handling and validation |
| `naming.md` | No-is-prefix booleans, context-driven names, collection plurals, verb prefixes, protocol naming, constants | Naming variables, methods, types |
| `protocols.md` | Protocol per dependency, default implementations, composition, mocking, associated types vs generics, protocol witness | Designing protocols, dependency injection, testing |
| `uikit_interop.md` | UIViewRepresentable, Coordinator pattern, UIViewControllerRepresentable, UIHostingController, retain cycle avoidance | Bridging UIKit and SwiftUI |

### Architecture

Service-level patterns:

| File | Content | Read when... |
|------|---------|--------------|
| `hexagonal_ddd.md` | **Primary architecture** - Ports & Adapters, domain/application/infrastructure layers, full directory structure | Any structural refactoring, setting up new service |
| `fastapi_web.md` | FastAPI inbound adapter patterns - thin routes, Depends, Pydantic schemas, exception handlers | Working with REST endpoints |
| `grpc_proxy.md` | gRPC outbound adapter patterns - proto conversion, error mapping, channel management | Working with gRPC clients |

**Note:** `fastapi_web.md` and `grpc_proxy.md` are adapter-specific supplements to `hexagonal_ddd.md`. Read the main architecture file first if restructuring.

## Quick Reference

| Refactoring type | Read these files |
|------------------|------------------|
| **Full service restructure** | `hexagonal_ddd.md` + `principles.md` |
| **FastAPI routes** | `fastapi_web.md` |
| **gRPC client** | `grpc_proxy.md` |
| **Method cleanup** | `method_structure.md` + `method_signature.md` |
| **Error handling** | `error_handling.md` |
| **Async code** | `async_patterns.md` |
| **Class restructure** | `class_body.md` + `principles.md` |
| **Naming issues** | `naming.md` |
| **Logging** | `logging.md` |
| **SwiftUI views** | `swift/elements/view_structure.md` |
| **Swift ViewModels** | `swift/elements/viewmodel_design.md` + `swift/principles.md` |
| **Swift async code** | `swift/elements/async_patterns.md` |
| **Swift error handling** | `swift/elements/error_handling.md` |
| **Swift naming** | `swift/elements/naming.md` |
| **Swift protocols/DI** | `swift/elements/protocols.md` |
| **UIKit interop** | `swift/elements/uikit_interop.md` |

## Adding New Languages

To add rules for a new language (e.g., Java, Rust):

1. Create `references/{language}/` directory
2. Add `principles.md` with language-specific principles
3. Add `elements/` with relevant code element rules
4. Add `architecture/` with service patterns
5. Update this navigation map
