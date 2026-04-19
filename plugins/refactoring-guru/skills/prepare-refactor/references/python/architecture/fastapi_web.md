# FastAPI Inbound Adapter Patterns

Patterns for implementing REST API inbound adapters with FastAPI. For overall architecture structure, see `../../common/architecture/hexagonal_ddd.md`.

## Thin Routes Pattern

Routes are thin HTTP handlers that delegate to application layer. NO business logic in routes.

```python
# Good - thin route, delegates to service
@router.get("/backlinks")
async def get_backlinks(
    url: str,
    limit: int = Query(default=10, ge=1, le=100),
    service: BacklinksService = Depends(get_backlinks_service),
) -> BacklinksResponse:
    return await service.get_backlinks_list(url, limit=limit)
```

```python
# Bad - business logic in route
@router.get("/backlinks")
async def get_backlinks(url: str) -> BacklinksResponse:
    validated_url = validate_url(url)  # Logic!
    client = GrpcClient()              # Creating dependencies!
    request = BasicRequest(target=validated_url, limit=10)
    items = []
    async for item in client.fetch(request):
        items.append(convert_item(item))  # Conversion logic!
    return BacklinksResponse(items=items)
```

## Dependency Injection with Depends

Use FastAPI's `Depends` to inject services. Makes testing easy.

```python
# dependencies.py
def get_dialogue_port() -> DialoguePort:
    return DialogueStorage()

def get_message_service(
    dialogue: DialoguePort = Depends(get_dialogue_port),
) -> MessageService:
    return MessageService(dialogue_port=dialogue)


# routes.py
@router.post("/messages")
async def create_message(
    request: MessageRequest,
    service: MessageService = Depends(get_message_service),
) -> MessageResponse:
    return await service.process_message(request.user_id, request.message)
```

## Testing with Dependency Overrides

```python
def test_get_backlinks():
    mock_service = AsyncMock(spec=BacklinksService)
    mock_service.get_backlinks_list.return_value = BacklinksResponse(items=[])

    app.dependency_overrides[get_backlinks_service] = lambda: mock_service

    response = client.get("/backlinks?url=example.com")
    assert response.status_code == 200
```

## Pydantic Schemas for Contracts

Define request/response schemas separately from domain models.

```python
# schemas/backlinks.py
from pydantic import BaseModel, Field


class BacklinkItem(BaseModel):
    source_url: str
    target_url: str
    anchor: str
    page_score: int = Field(ge=0, le=100)


class BacklinksResponse(BaseModel):
    items: list[BacklinkItem]


class BacklinksRequest(BaseModel):
    url: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort_direction: Literal['asc', 'desc'] = 'desc'
```

## Query Parameter Validation

Use `Query` for validation and documentation.

```python
@router.get("/search")
async def search(
    query: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Literal['relevance', 'date'] = Query(default='relevance'),
) -> SearchResponse:
    ...
```

## Exception Handlers

Register global exception handlers in `main.py` to convert domain exceptions to HTTP responses.

```python
# main.py
from app.core.domain.exceptions import NotFoundError, ValidationError


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )
```

## Router Organization

Group related endpoints in routers, mount in main app.

```python
# routes/backlinks.py
router = APIRouter(prefix="/backlinks", tags=["backlinks"])

@router.get("/")
async def list_backlinks(...): ...

@router.get("/{backlink_id}")
async def get_backlink(...): ...


# main.py
from app.adapters.inbound.rest.routes import backlinks, health

app.include_router(backlinks.router)
app.include_router(health.router)
```

## Lifespan for Startup/Shutdown (Preferred Pattern)

Use lifespan context manager for orchestrator and service initialization. This is the **preferred pattern** over lazy initialization or module-level singletons.

### Why Lifespan Over Alternatives

| Pattern | Problem |
|---------|---------|
| Lazy init (`if self._x is None`) | Mutable state, unpredictable timing, first-request latency |
| Module-level (`_x = create_x()`) | Runs at import time, no async support, no cleanup |
| **Lifespan** | Explicit lifecycle, async-ready, graceful shutdown ✓ |

### Basic Structure

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - all initialization in one place
    orchestrator = CoreOrchestrator()
    await orchestrator.start()
    app.state.orchestrator = orchestrator

    yield

    # Shutdown - cleanup resources
    await orchestrator.stop()


app = FastAPI(lifespan=lifespan)
```

### Dependencies Access app.state

```python
# dependencies.py
from fastapi import Request

from app.core.application import CoreOrchestrator
from app.core.ports.outbound import BacklinksPort, SpectrumPort


def get_orchestrator(request: Request) -> CoreOrchestrator:
    """Get orchestrator created at startup."""
    return request.app.state.orchestrator


def get_spectrum_port(request: Request) -> SpectrumPort:
    """Get port from orchestrator."""
    return request.app.state.orchestrator.spectrum


def get_backlinks_port(request: Request) -> BacklinksPort:
    return request.app.state.orchestrator.backlinks
```

### Anti-Pattern: Lazy Init in Dependencies

```python
# Bad - lazy initialization with global mutable state
_orchestrator: CoreOrchestrator | None = None

def get_orchestrator() -> CoreOrchestrator:
    global _orchestrator
    if _orchestrator is None:  # Mutable! Runs on first request!
        _orchestrator = CoreOrchestrator()
    return _orchestrator
```

### Anti-Pattern: Module-Level Eager Init

```python
# Bad - runs at import time, no async, no cleanup
_orchestrator = CoreOrchestrator()  # When does this run?

def get_orchestrator() -> CoreOrchestrator:
    return _orchestrator
```

### Testing with Lifespan

Override `app.state` or use dependency overrides:

```python
@pytest.fixture
def client(mock_orchestrator):
    app.state.orchestrator = mock_orchestrator
    with TestClient(app) as client:
        yield client

# Or use dependency overrides
app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
```

## Settings from Environment

Use Pydantic Settings for configuration.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
```
