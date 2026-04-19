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
└── java/
    ├── principles.md          # High-level style principles
    ├── elements/              # Code element patterns
    │   ├── method_signature.md
    │   ├── method_structure.md
    │   ├── error_handling.md
    │   ├── concurrency.md
    │   ├── class_body.md
    │   ├── naming.md
    │   ├── logging.md
    │   └── javadoc.md
    └── architecture/          # Service architecture patterns
        ├── hexagonal_ddd.md
        ├── spring_web.md
        └── grpc_proxy.md
```

## File Descriptions

### Principles (`principles.md`)

High-level style principles that apply broadly. Each language has its own principles file.

**Python:** Decorators for cross-cutting concerns, loose coupling, composition over inheritance, explicit over implicit, deferred computation.

**Java:** Final fields everywhere, no setters, no get prefix, constructor injection, telescoping constructors, sealed interfaces, records for data.

**Read when:** Starting any refactoring to understand overall philosophy.

### Elements (Python)

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

### Elements (Java)

| File | Content | Read when... |
|------|---------|--------------|
| `method_signature.md` | Enums, request records, overloads, Optional, naming patterns, domain types | Refactoring method signatures |
| `method_structure.md` | Single responsibility, method length, extraction, early returns, switch expressions | Splitting/refactoring method bodies |
| `error_handling.md` | @ControllerAdvice, domain exceptions, gRPC error mapping, interceptors | Touching try/catch, error flows |
| `concurrency.md` | Streams, CompletableFuture, virtual threads, semaphores, timeouts | Working with concurrent/async Java code |
| `class_body.md` | Final fields, constructor DI, telescoping constructors, records, sealed interfaces | Restructuring classes |
| `naming.md` | Context-driven names, no get prefix, conventions, method prefixes | Renaming variables/methods/classes |
| `logging.md` | SLF4J event-based logging, structured context, MDC, log levels | Adding/refactoring log statements |
| `javadoc.md` | Class/method Javadoc, @param/@return conventions, override skip rule | Adding/reviewing Javadoc comments |

### Architecture (Python)

Service-level patterns:

| File | Content | Read when... |
|------|---------|--------------|
| `hexagonal_ddd.md` | **Primary architecture** - Ports & Adapters, domain/application/infrastructure layers, full directory structure | Any structural refactoring, setting up new service |
| `fastapi_web.md` | FastAPI inbound adapter patterns - thin routes, Depends, Pydantic schemas, exception handlers | Working with Python REST endpoints |
| `grpc_proxy.md` | gRPC outbound adapter patterns - proto conversion, error mapping, channel management | Working with gRPC clients |

**Note:** `fastapi_web.md` and `grpc_proxy.md` are adapter-specific supplements to `hexagonal_ddd.md`. Read the main architecture file first if restructuring.

### Architecture (Java)

| File | Content | Read when... |
|------|---------|--------------|
| `hexagonal_ddd.md` | **Primary architecture** - Ports & Adapters with Spring Boot, records for domain models, interface ports, @Service/@Component wiring, testing | Any structural refactoring, setting up new Java service |
| `grpc_proxy.md` | gRPC client adapter patterns - proto conversion, error mapping, interceptors, channel management, streaming, timeouts | Working with Java gRPC clients |
| `spring_web.md` | Spring Boot REST patterns - thin controllers, constructor injection, records for DTOs, @ControllerAdvice, @ConfigurationProperties | Working with Java REST endpoints |

**Note:** `spring_web.md` and `grpc_proxy.md` are adapter-specific supplements to `hexagonal_ddd.md`. Read the main architecture file first if restructuring.

## Quick Reference

| Refactoring type | Read these files |
|------------------|------------------|
| **Full service restructure (Python)** | `python/architecture/hexagonal_ddd.md` + `python/principles.md` |
| **Full service restructure (Java)** | `java/architecture/hexagonal_ddd.md` + `java/principles.md` |
| **FastAPI routes** | `fastapi_web.md` |
| **Spring Boot controllers** | `spring_web.md` |
| **gRPC client (Python)** | `python/architecture/grpc_proxy.md` |
| **gRPC client (Java)** | `java/architecture/grpc_proxy.md` |
| **Method cleanup (Python)** | `python/elements/method_structure.md` + `python/elements/method_signature.md` |
| **Method cleanup (Java)** | `java/elements/method_structure.md` + `java/elements/method_signature.md` |
| **Error handling (Python)** | `python/elements/error_handling.md` |
| **Error handling (Java)** | `java/elements/error_handling.md` |
| **Async code (Python)** | `python/elements/async_patterns.md` |
| **Concurrency (Java)** | `java/elements/concurrency.md` |
| **Class restructure (Python)** | `python/elements/class_body.md` + `python/principles.md` |
| **Class restructure (Java)** | `java/elements/class_body.md` + `java/principles.md` |
| **Naming (Python)** | `python/elements/naming.md` |
| **Naming (Java)** | `java/elements/naming.md` |
| **Logging (Python)** | `python/elements/logging.md` |
| **Logging (Java)** | `java/elements/logging.md` |
| **Javadoc (Java)** | `java/elements/javadoc.md` |

## Adding New Languages

To add rules for a new language (e.g., Java, Rust):

1. Create `references/{language}/` directory
2. Add `principles.md` with language-specific principles
3. Add `elements/` with relevant code element rules
4. Add `architecture/` with service patterns
5. Update this navigation map
