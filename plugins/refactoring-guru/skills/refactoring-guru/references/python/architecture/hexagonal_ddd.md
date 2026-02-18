# Hexagonal Architecture with DDD (Ports & Adapters)

A clean architecture pattern that separates domain logic from infrastructure concerns. The domain core is isolated from external systems through well-defined ports and adapters.

## Directory Structure

```
service/
├── app/
│   ├── core/                           # Pure domain, no external dependencies
│   │   ├── domain/
│   │   │   ├── models/                 # Domain entities (dataclasses)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dialogue.py
│   │   │   │   ├── messages.py
│   │   │   │   └── requests.py
│   │   │   ├── exceptions.py           # Domain-specific exceptions
│   │   │   └── constants.py            # Domain constants
│   │   │
│   │   ├── application/                # Business logic orchestration
│   │   │   ├── __init__.py
│   │   │   ├── core_orchestrator.py    # Wires ports and adapters
│   │   │   ├── message_service.py      # Business logic
│   │   │   ├── managers/               # State/lifecycle managers
│   │   │   │   └── state_manager.py
│   │   │   ├── processors/             # Data processors
│   │   │   └── validators/             # Input validators
│   │   │       └── message_validator.py
│   │   │
│   │   ├── ports/                      # Interfaces (ABC)
│   │   │   ├── inbound/                # How outside world calls us
│   │   │   │   ├── __init__.py
│   │   │   │   └── api_port.py
│   │   │   └── outbound/               # How we call outside world
│   │   │       ├── __init__.py
│   │   │       ├── dialogue_port.py
│   │   │       ├── agent_port.py
│   │   │       └── session_port.py
│   │   │
│   │   └── infrastructure/             # Cross-cutting concerns
│   │       ├── healthcheck.py
│   │       └── observability.py
│   │
│   ├── adapters/                       # Implementations of ports
│   │   ├── inbound/                    # External → Core
│   │   │   ├── rest/                   # REST API adapter
│   │   │   │   └── routes.py
│   │   │   └── pubsub/                 # Message queue adapter
│   │   │       └── subscriber.py
│   │   │
│   │   └── outbound/                   # Core → External
│   │       ├── database/               # Database adapter
│   │       │   └── dialogue_storage.py
│   │       ├── agent/                  # AI agent adapter
│   │       │   └── agent_adapter.py
│   │       └── infrastructure/         # Infrastructure adapters
│   │           └── redis_client.py
│   │
│   ├── config/                         # Configuration
│   │   └── settings.py
│   │
│   └── main.py                         # Application entry point
│
└── tests/
    ├── unit/
    └── integration/
```

## Layer Responsibilities

### Domain Layer (`core/domain/`)

Pure business entities with no dependencies on external systems. Only Python stdlib.

```python
# core/domain/models/dialogue.py
from dataclasses import dataclass


@dataclass
class DialogueDeletionResult:
    """Result of dialogue deletion operation."""
    deleted_count: int
    success: bool = True
    error: str | None = None
```

```python
# core/domain/exceptions.py
class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class ValidationError(DomainException):
    """Raised when validation fails."""
    pass


class NotFoundError(DomainException):
    """Raised when entity not found."""
    pass
```

### Ports Layer (`core/ports/`)

Abstract interfaces that define contracts. No implementations.

**Outbound ports** - interfaces for external dependencies (what the core needs from outside):

```python
# core/ports/outbound/dialogue_port.py
from abc import ABC, abstractmethod


class DialoguePort(ABC):
    """
    Port for managing user dialogues.

    This port defines how the core application interacts with dialogue storage.
    """

    @abstractmethod
    async def ensure_active(self, user_id: int) -> str:
        """
        Get the active dialogue for a user or create a new one.

        Args:
            user_id: The user identifier

        Returns:
            The dialogue_id as a string (UUID format)
        """

    @abstractmethod
    async def find_active(self, user_id: int) -> str | None:
        """Find the active dialogue for a user if one exists."""

    @abstractmethod
    async def soft_delete(self, user_id: int) -> int:
        """Soft delete the active dialogue for a user."""
```

**Inbound ports** - interfaces for incoming requests (how outside calls the core):

```python
# core/ports/inbound/api_port.py
from abc import ABC, abstractmethod
from app.core.domain.models import MessageRequest, MessageResponse


class ApiPort(ABC):
    """Port for API operations."""

    @abstractmethod
    async def process_message(self, request: MessageRequest) -> MessageResponse:
        """Process an incoming message request."""
```

### Application Layer (`core/application/`)

Orchestrates domain logic, uses ports for external interactions.

```python
# core/application/core_orchestrator.py
from app.core.ports.outbound import (
    AgentPort,
    DialoguePort,
    SessionPort,
)


class CoreOrchestrator:
    """
    Orchestrates the hexagonal architecture components.

    Responsible for:
    - Creating and wiring ports and adapters
    - Managing component lifecycle (start/stop)
    - Providing health check functionality
    """

    def __init__(self) -> None:
        # Adapters are injected, typed as ports
        self.agent_adapter: AgentPort = AgnoAgentAdapter()
        self.dialogue_storage: DialoguePort = DialogueStorage()
        self.session_service: SessionPort = SessionService()

        # Services use ports, not concrete implementations
        self.message_service = MessageService(
            agent_port=self.agent_adapter,
            dialogue_port=self.dialogue_storage,
            session_port=self.session_service,
        )

    async def start(self) -> None:
        """Start all components."""
        ...

    async def stop(self) -> None:
        """Stop all components gracefully."""
        ...
```

```python
# core/application/message_service.py
class MessageService:
    """
    Business logic for message processing.

    Uses ports for all external interactions.
    """

    def __init__(
        self,
        agent_port: AgentPort,
        dialogue_port: DialoguePort,
        session_port: SessionPort,
    ) -> None:
        self._agent = agent_port
        self._dialogue = dialogue_port
        self._session = session_port

    async def process_message(
        self,
        user_id: int,
        message: str,
    ) -> MessageResponse:
        """Process user message through the agent."""
        # Get or create dialogue
        dialogue_id = await self._dialogue.ensure_active(user_id)

        # Get or create session
        session_id = await self._session.get_or_create(user_id, dialogue_id)

        # Process through agent
        response = await self._agent.process_message(
            user_id=str(user_id),
            message=message,
            session_id=session_id,
            context={},
        )

        return MessageResponse(
            content=response.content,
            dialogue_id=dialogue_id,
        )
```

### Adapters Layer (`adapters/`)

Concrete implementations of ports.

**Outbound adapter** (implements port interface):

```python
# adapters/outbound/database/dialogue_storage.py
import asyncpg
from app.core.ports.outbound.dialogue_port import DialoguePort


class DialogueStorage(DialoguePort):
    """
    Dialogue storage using PostgreSQL.

    Implements DialoguePort with direct async SQL queries.
    """

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Lazy pool initialization."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=settings.postgres.host,
                port=settings.postgres.port,
                database=settings.postgres.name,
            )
        return self._pool

    async def ensure_active(self, user_id: int) -> str:
        """Get or create active dialogue."""
        pool = await self._get_pool()

        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT dialogue_id FROM dialogue
                WHERE user_id = $1 AND deleted = false
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id,
            )

            if row:
                return str(row['dialogue_id'])

            # Create new dialogue
            new_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO dialogue (dialogue_id, user_id, created_at)
                VALUES ($1, $2, $3)
                """,
                new_id, user_id, datetime.now(UTC),
            )
            return str(new_id)

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
```

**Inbound adapter** (calls application layer):

```python
# adapters/inbound/rest/routes.py
from fastapi import APIRouter, Depends
from app.core.application.message_service import MessageService


router = APIRouter()


@router.post("/messages")
async def send_message(
    request: MessageRequest,
    service: MessageService = Depends(get_message_service),
) -> MessageResponse:
    """REST endpoint that delegates to application layer."""
    return await service.process_message(
        user_id=request.user_id,
        message=request.message,
    )
```

## Key Patterns

### Pattern: Dependency Inversion

Core depends on abstractions (ports), not concrete implementations (adapters).

```python
# Good - depends on port (abstraction)
class MessageService:
    def __init__(self, dialogue_port: DialoguePort):
        self._dialogue = dialogue_port

# Bad - depends on concrete implementation
class MessageService:
    def __init__(self):
        self._dialogue = DialogueStorage()  # Concrete!
```

### Pattern: Ports as ABC

Ports are abstract base classes with clear contracts.

```python
from abc import ABC, abstractmethod


class DialoguePort(ABC):
    """Port defines the contract."""

    @abstractmethod
    async def ensure_active(self, user_id: int) -> str:
        """Must be implemented by adapters."""
```

### Pattern: Adapter Implements Port

Adapters inherit from ports and provide concrete implementation.

```python
class DialogueStorage(DialoguePort):
    """Adapter implements the port contract."""

    async def ensure_active(self, user_id: int) -> str:
        # Concrete PostgreSQL implementation
        ...
```

### Pattern: Orchestrator Wires Dependencies

One place where adapters are instantiated and wired together.

```python
class CoreOrchestrator:
    def __init__(self):
        # Create adapters (concrete)
        dialogue_adapter = DialogueStorage()

        # Inject as ports (abstract)
        self.message_service = MessageService(
            dialogue_port=dialogue_adapter,
        )
```

## Benefits

1. **Testability** - Mock ports for unit tests, no real databases needed
2. **Flexibility** - Swap adapters without changing domain logic
3. **Clarity** - Clear boundaries between layers
4. **Independence** - Domain logic has no external dependencies

## Testing

```python
# Unit test with mock port
async def test_process_message():
    mock_dialogue = AsyncMock(spec=DialoguePort)
    mock_dialogue.ensure_active.return_value = "dialogue-123"

    service = MessageService(dialogue_port=mock_dialogue)
    result = await service.process_message(user_id=1, message="hello")

    mock_dialogue.ensure_active.assert_called_once_with(1)
```
