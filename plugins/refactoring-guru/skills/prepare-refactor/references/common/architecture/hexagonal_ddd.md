# Hexagonal Architecture with DDD (Ports & Adapters)

A language-agnostic clean-architecture pattern that isolates domain logic from infrastructure. The core talks to the outside world exclusively through **ports** (interfaces); **adapters** implement those ports for concrete technologies (databases, HTTP, queues, RPC).

Each `##` heading below is a rule. A reviewer checks every file in scope against every heading.

## Directory Structure

The codebase is split into three concentric zones:

```
service/
├── core/                           # Pure domain. No I/O. No framework types.
│   ├── domain/                     # Entities, value objects, domain errors
│   ├── ports/                      # Interfaces
│   │   ├── inbound/                # How the outside world calls us
│   │   └── outbound/               # How we call the outside world
│   └── application/                # Use cases / services orchestrating ports
│
├── adapters/                       # Port implementations (the only code with I/O)
│   ├── inbound/                    # REST, gRPC, message subscribers, CLI
│   └── outbound/                   # DB clients, HTTP clients, RPC stubs, caches
│
└── config/                         # Composition root: constructs adapters, injects them behind ports
```

**Rule:** `core/` contains no imports from infrastructure libraries (DB drivers, HTTP frameworks, RPC stubs). If a file under `core/` imports a concrete infrastructure type, it belongs in `adapters/` — move it.

## Dependency Direction

Dependencies point **inward** only. Core ← Ports ← Application → (callers/adapters implement outward interfaces).

```
          External world (HTTP, DB, queues, RPC peers)
                  │                       ▲
                  ▼                       │
            ┌─────────────┐         ┌─────────────┐
            │   inbound   │         │   outbound  │
            │   ADAPTER   │         │   ADAPTER   │   ← implements outbound port
            └──────┬──────┘         └──────▲──────┘
                   │ calls                 │ implements
                   ▼                       │
            ┌─────────────────────────────────────┐
            │       APPLICATION (use cases)       │
            │  depends on PORTS, never adapters   │
            └──────┬──────────────────────▲──────┘
                   │ uses                  │ uses
                   ▼                       │
            ┌──────────────┐       ┌─────────────┐
            │ DOMAIN MODEL │       │    PORTS    │
            └──────────────┘       └─────────────┘
```

**Rule:** The domain and application layers never import from `adapters/` or from infrastructure libraries. Imports must only flow outside → inside.

## Ports Are Interfaces

Ports are declared in `core/ports/`, as abstract interfaces (ABC / `protocol` / `interface` / `trait` — whichever the language provides). Ports contain only signatures and docstrings. They never contain implementation logic, I/O, or reference infrastructure types.

- **Outbound ports** describe what the core needs from the outside (storage, clients, notifiers).
- **Inbound ports** describe the use cases the core exposes to the outside (for testing, alternative frontends, or framework-independent handlers).

**Rule:** A port file contains one interface definition and method signatures only. Any concrete logic, state, or framework import in a port is a violation.

## Adapters Implement Ports and Translate

Every adapter has two responsibilities and nothing else:

1. Implement a port interface.
2. Translate between the outside representation (protobuf, SQL rows, DTOs, HTTP payloads) and domain types.

```
class SomeAdapter implements SomeOutboundPort:
    def do_thing(request: DomainRequest) -> DomainResult:
        external_req = translate_to_external(request)        # domain → external
        external_resp = external_client.call(external_req)   # one real call
        return translate_to_domain(external_resp)            # external → domain
```

**Rule:** Inside an adapter, domain objects never cross into external calls untranslated, and external objects never leave the adapter. Translation at the boundary is the adapter's whole job.

## Adapters Are Not Pass-Throughs

A common anti-pattern is an adapter that calls a service that calls the stub — with no translation happening in the adapter. In that shape, the service is doing adapter work (talking protobuf / SQL) and the adapter adds nothing.

```
# ❌ Wrong — adapter forwards, service handles protobuf
class Adapter(Port):
    def get(x):
        return self._service.get(x)        # pass-through only

class Service:
    def get(x):
        return self._stub.Call(ProtoReq(x))  # protobuf in the service

# ✅ Right — service depends on port; adapter owns translation
class Service:
    def __init__(self, port: Port): ...
    def analyze(x):
        data = self._port.get(x)           # port call, domain types
        return compute(data)

class Adapter(Port):
    def get(x):
        req = to_proto(x)
        resp = self._stub.Call(req)
        return to_domain(resp)
```

**Rule:** If an adapter method does nothing except delegate to another object, it's a sign the layers are inverted. Either push translation into the adapter, or drop the adapter and have the service implement the port directly (see next rule).

## When to Skip the Application Layer

If a use case has no business logic beyond "fetch, translate, return", the application/service layer adds noise. Two acceptable shapes:

- **A:** Inbound adapter calls the outbound port directly (no service). Adapter still implements the outbound port and does translation.
- **B:** Collapse adapter into a service that implements the outbound port — one class does both translation and (eventual) business logic.

Both keep the dependency direction correct. Avoid a dedicated service class whose body is a single passthrough call.

**Rule:** An application/service class with only forwarding methods (no validation, composition, or business logic) is a deletable layer. Remove it and let the callers use the port directly.

## Domain Models Are Framework-Free

Domain models (entities, value objects) are declared with the plainest tools the language offers (records/dataclasses/structs/case-classes). They never inherit from ORM bases, never carry protobuf, and never carry HTTP/request annotations.

**Rule:** A domain model file imports from the standard library (or the language's built-in data-class mechanism) only. Any ORM / protobuf / web-framework import under `core/domain/` is a violation.

## Composition Root Wires the Graph

A single place — typically `config/` or the application entry point — constructs the concrete adapters and injects them as ports into the services. Nothing else instantiates adapters by concrete class.

```
# Composition root
dialogue_adapter = PostgresDialogueAdapter(...)   # concrete
message_service  = MessageService(
    dialogue_port = dialogue_adapter,             # injected as port type
)
```

**Rule:** Outside the composition root, code depends on port types only. Constructing or `new`-ing a concrete adapter inside a service, controller, or domain object is a violation.

## Inbound Adapters Are Thin

Inbound adapters (REST controllers, gRPC handlers, message subscribers) translate the transport into a port / service call and return. They do no business logic, no validation beyond shape checking, no multi-step orchestration.

**Rule:** An inbound adapter method body beyond ~10 lines, containing business branches, aggregations, or multi-step orchestration, belongs in the application layer — move it behind an inbound port or service method.

## Testing Reflects the Architecture

- Domain and application code is tested with fakes / mocks of port interfaces. No real databases, HTTP, or network in unit tests.
- Adapters are tested against the real (or containerised) external system — their whole job is translation correctness.
- Integration tests wire real adapters through the composition root.

**Rule:** Unit tests for application/service classes that spin up real infrastructure (DB, HTTP, gRPC) indicate the service is coupled to an adapter. Extract the dependency behind a port and mock the port.

## Benefits Check

A correct hexagonal split gives you:

1. **Swap-ability** — replacing Postgres with Dynamo means writing one new adapter. No core changes.
2. **Test speed** — unit tests run without network/disk.
3. **Readability** — the domain reads as prose about business rules, not framework incantations.
4. **Onboarding** — new contributors can understand a use case by reading its service + ports, without tracing through framework plumbing.

If any of these don't hold for your code, one of the rules above is being violated. Find which.
