# gRPC Outbound Adapter Patterns

Patterns for implementing gRPC client adapters. For overall architecture structure, see `hexagonal_ddd.md`.

## Adapter Structure

gRPC adapter implements an outbound port and handles all gRPC-specific concerns.

```python
# adapters/outbound/agent/agent_adapter.py
from app.core.ports.outbound.agent_port import AgentPort


class GrpcAgentAdapter(AgentPort):
    """
    gRPC adapter for agent service.

    Implements AgentPort, handles:
    - Channel management
    - Proto conversion
    - Error mapping
    """

    def __init__(self, channel: grpc.aio.Channel):
        self._stub = AgentServiceStub(channel)

    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: str,
        context: dict[str, Any],
    ) -> AgentResponse:
        request = self._to_proto(user_id, message, session_id)
        proto_response = await self._stub.Process(request)
        return self._from_proto(proto_response)
```

## Proto Conversion

Keep conversion logic in the adapter. Domain models stay clean.

```python
class GrpcBacklinksAdapter(BacklinksPort):
    """Converts between domain models and protobuf."""

    def _to_proto(self, url: str, limit: int) -> BacklinksRequest:
        """Domain → Proto."""
        return BacklinksRequest(
            target=url,
            limit=limit,
            export_columns=['source_url', 'target_url', 'anchor'],
        )

    def _from_proto(self, proto: BacklinkProto) -> BacklinkItem:
        """Proto → Domain."""
        return BacklinkItem(
            source_url=proto.source_url,
            target_url=proto.target_url,
            anchor=proto.anchor,
            page_score=proto.page_score,
        )

    async def get_backlinks(self, url: str, limit: int) -> list[BacklinkItem]:
        request = self._to_proto(url, limit)
        return [
            self._from_proto(proto)
            async for proto in self._stub.Backlinks(request)
        ]
```

## gRPC Error Mapping

Map gRPC status codes to domain exceptions.

```python
import grpc
from app.core.domain.exceptions import NotFoundError, ServiceUnavailableError


GRPC_TO_DOMAIN = {
    grpc.StatusCode.NOT_FOUND: NotFoundError,
    grpc.StatusCode.INVALID_ARGUMENT: ValidationError,
    grpc.StatusCode.UNAVAILABLE: ServiceUnavailableError,
    grpc.StatusCode.DEADLINE_EXCEEDED: TimeoutError,
}


def map_grpc_error(error: grpc.aio.AioRpcError) -> Exception:
    """Convert gRPC error to domain exception."""
    exception_class = GRPC_TO_DOMAIN.get(error.code(), ServiceError)
    return exception_class(error.details())
```

## Error Handler Decorator

Centralize gRPC error handling in a decorator.

```python
def grpc_error_handler(
    operation: str,
    default_factory: Callable[[], T],
) -> Callable[...]:
    """Decorator for gRPC error handling."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            try:
                return await func(self, *args, **kwargs)
            except grpc.aio.AioRpcError as e:
                logger.warning(
                    f"event={operation}_grpc_error",
                    code=e.code().name,
                    details=e.details(),
                )
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    return default_factory()
                raise map_grpc_error(e)
        return wrapper
    return decorator


# Usage
class GrpcBacklinksAdapter(BacklinksPort):
    @grpc_error_handler('get_backlinks', list)
    async def get_backlinks(self, url: str, limit: int) -> list[BacklinkItem]:
        ...
```

## Streaming Responses

Use async comprehensions for streaming gRPC responses.

```python
async def get_backlinks(self, url: str, limit: int) -> list[BacklinkItem]:
    request = self._to_proto(url, limit)

    # Good - async comprehension
    return [
        self._from_proto(proto)
        async for proto in self._stub.Backlinks(request)
    ]
```

## Channel Management

Manage gRPC channel lifecycle properly.

```python
# Lazy channel creation
class GrpcAdapter:
    def __init__(self, host: str):
        self._host = host
        self._channel: grpc.aio.Channel | None = None

    async def _get_channel(self) -> grpc.aio.Channel:
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(
                self._host,
                options=[
                    ('grpc.keepalive_time_ms', 30000),
                    ('grpc.keepalive_timeout_ms', 10000),
                ],
            )
        return self._channel

    async def close(self) -> None:
        if self._channel:
            await self._channel.close()
            self._channel = None
```

## Channel as Dependency

Inject channel through orchestrator for testability.

```python
# orchestrator.py
class CoreOrchestrator:
    def __init__(self):
        channel = grpc.aio.insecure_channel(settings.grpc_host)
        self.backlinks_adapter = GrpcBacklinksAdapter(channel)

    async def stop(self):
        await self.backlinks_adapter.close()
```

## Timeouts

Always set deadlines for gRPC calls.

```python
async def get_backlinks(self, url: str, limit: int) -> list[BacklinkItem]:
    request = self._to_proto(url, limit)

    # Set timeout
    try:
        return [
            self._from_proto(proto)
            async for proto in self._stub.Backlinks(
                request,
                timeout=30.0,  # 30 seconds
            )
        ]
    except grpc.aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            logger.warning("event=backlinks_grpc_timeout", url=url)
            return []
        raise
```

## Metadata/Headers

Pass metadata for tracing and authentication.

```python
async def get_backlinks(
    self,
    url: str,
    limit: int,
    request_id: str,
) -> list[BacklinkItem]:
    request = self._to_proto(url, limit)

    metadata = [
        ('x-request-id', request_id),
        ('authorization', f'Bearer {self._token}'),
    ]

    return [
        self._from_proto(proto)
        async for proto in self._stub.Backlinks(request, metadata=metadata)
    ]
```

## Testing with Mock Stub

Mock the stub for unit tests.

```python
@pytest.fixture
def mock_stub():
    stub = AsyncMock()
    stub.Backlinks.return_value = AsyncIterator([
        BacklinkProto(source_url="http://a.com", page_score=50),
        BacklinkProto(source_url="http://b.com", page_score=30),
    ])
    return stub


async def test_get_backlinks(mock_stub):
    adapter = GrpcBacklinksAdapter.__new__(GrpcBacklinksAdapter)
    adapter._stub = mock_stub

    result = await adapter.get_backlinks("example.com", limit=10)

    assert len(result) == 2
    assert result[0].source_url == "http://a.com"
```
