# Logging Patterns

## Use @Slf4j Instead of a Logger Field

Declare the logger with Lombok's `@Slf4j` on the class. Do not declare `private static final Logger log = ...` by hand.

```java
// Bad - manual logger field
public class BacklinksService {
    private static final Logger log = LoggerFactory.getLogger(BacklinksService.class);
}

// Good - @Slf4j injects the same `log` field
@Slf4j
public class BacklinksService {
}
```

## Event-Based Log Messages

Use `event=` prefix for log messages. The event name must identify the exact location -- someone reading the log should know exactly where to look.

```java
// Good - event identifies exact location
log.info("event=fetch_backlinks_completed url={} count={}", url, items.size());
log.warn("event=fetch_backlinks_retry attempt={} error={}", attempt, e.getMessage());
log.error("event=fetch_backlinks_grpc_error code={} details={}", status.getCode(), status.getDescription());

// Bad - vague event, could be anywhere
log.info("event=fetch_completed url={} count={}", url, items.size());
log.warn("event=retry_failed attempt={} error={}", attempt, e.getMessage());
log.error("event=grpc_error code={}", status.getCode());

// Bad - free-form messages
log.info("Fetched {} backlinks for {}", items.size(), url);
```

## Structured Logging

Pass context as SLF4J parameters, not via string concatenation. For cross-cutting context, use MDC.

```java
// Good - SLF4J parameterized logging
log.info("event=process_order_completed user_id={} duration_ms={} status={}",
    userId, duration, response.statusCode());

// Good - MDC for cross-cutting context
MDC.put("request_id", requestId);
MDC.put("user_id", String.valueOf(userId));
try {
    log.info("event=process_order_started");
    var result = processOrder(order);
    log.info("event=process_order_completed duration_ms={}", duration);
} finally {
    MDC.clear();
}

// Bad - string concatenation
log.info("Request completed for user " + userId + " in " + duration + "ms with status " + status);

// Bad - string interpolation defeats lazy evaluation
log.debug("event=fetch_backlinks_detail payload=%s".formatted(payload));
```

## Log Levels

| Level | Use for | Example |
|---|---|---|
| `debug` | Development details | `event=fetch_backlinks_cache_hit` |
| `info` | Normal operations | `event=fetch_backlinks_started`, `event=fetch_backlinks_completed` |
| `warn` | Recoverable issues | `event=fetch_backlinks_retry`, `event=fetch_backlinks_fallback` |
| `error` | Failures requiring attention | `event=fetch_backlinks_failed`, `event=process_order_validation_error` |

## Event Naming

Use snake_case for event names. Include the operation name so the log pinpoints the exact code location.

```java
// Good - operation + what happened
"event=fetch_backlinks_started"
"event=fetch_backlinks_cache_miss"
"event=fetch_backlinks_retry_succeeded"
"event=fetch_backlinks_timeout"

// Bad - missing operation context
"event=cache_miss"         // Which cache? Which operation?
"event=retry_succeeded"    // Retry of what?
"event=grpc_timeout"       // Which gRPC call?
```

## Logging in Error Handlers

Log before re-throwing. The event name should include the operation.

```java
public List<BacklinkItem> fetchBacklinks(String url) {
    try {
        return backlinkClient.fetch(url);
    } catch (StatusRuntimeException e) {
        log.warn("event=fetch_backlinks_grpc_error code={} details={} url={}",
            e.getStatus().getCode(), e.getStatus().getDescription(), url);
        throw e;
    }
}
```

## Avoid Logging Sensitive Data

Never log credentials, tokens, or PII.

```java
// Bad - logs sensitive data
log.info("event=authenticate_user_started token={} password={}", token, password);

// Good - redact or omit sensitive fields
log.info("event=authenticate_user_started user_id={} token_prefix={}",
    userId, token.substring(0, 8));
```
