# Logging Patterns

## Event-Based Log Messages

Use `event=` prefix for log messages. The event name must identify the exact location - someone reading the log should know exactly where to look.

```python
# Good - event identifies exact location
logger.info("event=fetch_backlinks_completed", url=url, count=len(items))
logger.warning("event=fetch_backlinks_retry", attempt=3, error=str(e))
logger.error("event=fetch_backlinks_grpc_error", code=e.code().name, details=e.details())

# Bad - vague event, could be anywhere
logger.info("event=fetch_completed", url=url, count=len(items))
logger.warning("event=retry_failed", attempt=3, error=str(e))
logger.error("event=grpc_error", code=e.code().name, details=e.details())

# Bad - free-form messages
logger.info(f"Fetched {len(items)} backlinks for {url}")
```

## Structured Logging

Pass context as keyword arguments, not in the message string.

```python
# Good - structured context
logger.info(
    "event=process_order_completed",
    user_id=user_id,
    duration_ms=duration,
    status=response.status_code,
)

# Bad - context buried in string
logger.info(f"Request completed for user {user_id} in {duration}ms with status {status}")
```

## Log Levels

| Level | Use for | Example |
|-------|---------|---------|
| `debug` | Development details | `event=fetch_backlinks_cache_hit` |
| `info` | Normal operations | `event=fetch_backlinks_started`, `event=fetch_backlinks_completed` |
| `warning` | Recoverable issues | `event=fetch_backlinks_retry`, `event=fetch_backlinks_fallback` |
| `error` | Failures requiring attention | `event=fetch_backlinks_failed`, `event=process_order_validation_error` |

## Event Naming

Use snake_case for event names. Include the operation name so the log pinpoints the exact code location.

```python
# Good - operation + what happened
"event=fetch_backlinks_started"
"event=fetch_backlinks_cache_miss"
"event=fetch_backlinks_retry_succeeded"
"event=fetch_backlinks_timeout"

# Bad - missing operation context
"event=cache_miss"        # Which cache? Which operation?
"event=retry_succeeded"   # Retry of what?
"event=grpc_timeout"      # Which gRPC call?
```

## Logging in Error Handlers

Log before re-raising or returning. The event name should include the operation.

```python
async def _fetch_backlinks(self, url: str) -> list[BacklinkItem]:
    try:
        return await self._do_fetch(url)
    except grpc.aio.AioRpcError as e:
        logger.warning(
            "event=fetch_backlinks_grpc_error",
            code=e.code().name,
            details=e.details(),
            url=url,
        )
        raise
```

## Avoid Logging Sensitive Data

Never log credentials, tokens, or PII.

```python
# Bad - logs sensitive data
logger.info("event=authenticate_user_started", token=token, password=password)

# Good - redact or omit sensitive fields
logger.info("event=authenticate_user_started", user_id=user_id, token_prefix=token[:8])
```
