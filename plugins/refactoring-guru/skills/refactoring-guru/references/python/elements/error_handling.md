# Error Handling Rules

## Decorator-Based Error Handling

Centralize try/except in decorators. Fetch methods stay clean and focused on the happy path.

```python
# Bad - scattered try/except
async def _fetch_items(self, url: str) -> list[Item]:
    try:
        return [item async for item in self._stub.List(request)]
    except grpc.aio.AioRpcError as e:
        self._log_grpc_error('items', url, e)
        return []

# Good - decorator handles errors
@grpc_error_handler('items', list)
async def _fetch_items(self, url: str) -> list[Item]:
    return [item async for item in self._stub.List(request)]
```

## gRPC Error Handler Decorator Pattern

```python
from functools import wraps
from typing import TypeVar, Callable, Any
from collections.abc import Coroutine
import grpc.aio

T = TypeVar('T')


def grpc_error_handler(
    operation: str,
    default_factory: Callable[[], T],
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]],
    Callable[..., Coroutine[Any, Any, T]],
]:
    """Handles gRPC errors and returns default value on failure."""
    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            url = kwargs.get('url', args[0] if args else 'unknown')
            try:
                return await func(self, *args, **kwargs)
            except grpc.aio.AioRpcError as e:
                self._log_grpc_error(operation, url, e)
                return default_factory()
        return wrapper
    return decorator
```

## HTTP Error Handler Decorator Pattern

```python
from functools import wraps
from typing import TypeVar, Callable, Any
from collections.abc import Coroutine
import httpx

T = TypeVar('T')


def http_error_handler(
    operation: str,
    default_factory: Callable[[], T],
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]],
    Callable[..., Coroutine[Any, Any, T]],
]:
    """Handles HTTP errors and returns default value on failure."""
    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            try:
                return await func(self, *args, **kwargs)
            except httpx.HTTPStatusError as e:
                logger.warning(f"event={operation}_http_error", status=e.response.status_code)
                return default_factory()
            except httpx.RequestError as e:
                logger.warning(f"event={operation}_request_error", error=str(e))
                return default_factory()
        return wrapper
    return decorator
```

## Logging Outside Error Handling

Success logs should be after data fetch, not inside try blocks. This keeps logging separate from error handling.

```python
# Bad - mixed concerns
try:
    items = await self._fetch_backlinks()
    logger.info("event=fetch_backlinks_completed", count=len(items))  # Inside try
except: ...

# Good - separated concerns
items = await self._fetch_backlinks()  # Decorator handles errors
logger.info("event=fetch_backlinks_completed", count=len(items))  # Always runs after success
```

## Specific Exception Types

Catch specific exceptions, not bare `except`. Let unexpected errors propagate.

```python
# Bad - catches everything
try:
    result = await api.call()
except:
    return None

# Good - specific exceptions
try:
    result = await api.fetch_user(user_id)
except httpx.TimeoutException:
    logger.warning("event=fetch_user_timeout")
    return None
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        return None
    raise  # Re-raise unexpected status codes
```

## Error Context in Logs

Include relevant context when logging errors. Use structured logging with key-value pairs.

```python
# Bad - minimal context
logger.error("event=request_failed")

# Good - rich context
logger.error(
    "event=fetch_users_failed",
    url=url,
    status_code=e.response.status_code,
    error=str(e),
)
```
