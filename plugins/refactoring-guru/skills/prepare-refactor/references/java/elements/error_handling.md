# Error Handling Rules

## Centralized Exception Handling with @ControllerAdvice

Centralize error handling in a single place using Spring's `@ControllerAdvice` or AOP interceptors. Individual methods stay clean and focused on the happy path.

```java
// Bad - scattered try/catch in every method
@RestController
public class BacklinkController {
    public List<BacklinkItem> fetchBacklinks(String url) {
        try {
            return backlinkService.fetch(url);
        } catch (StatusRuntimeException e) {
            log.warn("event=fetch_backlinks_grpc_error code={}", e.getStatus().getCode());
            return List.of();
        }
    }

    public List<Domain> fetchDomains(String query) {
        try {
            return domainService.search(query);
        } catch (StatusRuntimeException e) {
            log.warn("event=fetch_domains_grpc_error code={}", e.getStatus().getCode());
            return List.of();
        }
    }
}

// Good - centralized handler, methods stay clean
@RestController
public class BacklinkController {
    public List<BacklinkItem> fetchBacklinks(String url) {
        return backlinkService.fetch(url);
    }

    public List<Domain> fetchDomains(String query) {
        return domainService.search(query);
    }
}

@ControllerAdvice
public class GrpcExceptionHandler {
    @ExceptionHandler(StatusRuntimeException.class)
    public ResponseEntity<ErrorResponse> handleGrpcError(StatusRuntimeException e) {
        var status = e.getStatus();
        log.warn("event=grpc_error_handled code={} description={}", status.getCode(), status.getDescription());
        return switch (status.getCode()) {
            case NOT_FOUND -> ResponseEntity.notFound().build();
            case UNAVAILABLE -> ResponseEntity.status(503).body(new ErrorResponse("Service unavailable"));
            default -> ResponseEntity.internalServerError().body(new ErrorResponse("Internal error"));
        };
    }
}
```

For gRPC services, use interceptors instead of `@ControllerAdvice`:

```java
// Good - gRPC interceptor centralizes error handling
public class GrpcErrorInterceptor implements ServerInterceptor {
    @Override
    public <Req, Resp> ServerCall.Listener<Req> interceptCall(
            ServerCall<Req, Resp> call, Metadata headers, ServerCallHandler<Req, Resp> next) {
        return new ForwardingServerCallListener.SimpleForwardingServerCallListener<>(
                next.startCall(call, headers)) {
            @Override
            public void onHalfClose() {
                try {
                    super.onHalfClose();
                } catch (DomainNotFoundException e) {
                    call.close(Status.NOT_FOUND.withDescription(e.getMessage()), new Metadata());
                } catch (ValidationException e) {
                    call.close(Status.INVALID_ARGUMENT.withDescription(e.getMessage()), new Metadata());
                }
            }
        };
    }
}
```

## Custom Domain Exceptions

Define domain-specific exceptions extending `RuntimeException`. Keep them focused on one failure reason.

```java
// Bad - generic exception with error codes
public class ServiceException extends RuntimeException {
    private final int errorCode;
    public ServiceException(String message, int errorCode) {
        super(message);
        this.errorCode = errorCode;
    }
}
// Usage: throw new ServiceException("Not found", 404);

// Good - specific domain exceptions
public class BacklinkNotFoundException extends RuntimeException {
    private final String url;

    public BacklinkNotFoundException(String url) {
        super("Backlinks not found for URL: " + url);
        this.url = url;
    }

    public String url() { return url; }
}

public class DomainQuotaExceededException extends RuntimeException {
    private final String domain;
    private final int limit;

    public DomainQuotaExceededException(String domain, int limit) {
        super("Quota exceeded for domain %s (limit: %d)".formatted(domain, limit));
        this.domain = domain;
        this.limit = limit;
    }

    public String domain() { return domain; }
    public int limit() { return limit; }
}
```

## Specific Exception Types

Catch specific exceptions, not bare `Exception`. Let unexpected errors propagate.

```java
// Bad - catches everything
public Optional<User> fetchUser(int userId) {
    try {
        return Optional.of(client.getUser(userId));
    } catch (Exception e) {
        return Optional.empty();
    }
}

// Good - specific exceptions with specific handling
public Optional<User> fetchUser(int userId) {
    try {
        return Optional.of(client.getUser(userId));
    } catch (StatusRuntimeException e) {
        if (e.getStatus().getCode() == Status.Code.NOT_FOUND) {
            return Optional.empty();
        }
        throw e;  // Re-throw unexpected gRPC errors
    }
}
```

## Logging Outside Error Handling

Success logs should be after the call, not inside try blocks. This keeps logging separate from error handling.

```java
// Bad - mixed concerns
public List<BacklinkItem> fetchBacklinks(String url) {
    try {
        var items = backlinkClient.fetch(url);
        log.info("event=fetch_backlinks_completed url={} count={}", url, items.size());  // Inside try
        return items;
    } catch (StatusRuntimeException e) {
        log.warn("event=fetch_backlinks_grpc_error url={}", url);
        return List.of();
    }
}

// Good - separated concerns (interceptor handles errors)
public List<BacklinkItem> fetchBacklinks(String url) {
    var items = backlinkClient.fetch(url);
    log.info("event=fetch_backlinks_completed url={} count={}", url, items.size());
    return items;
}
```

## Error Context in Logs

Include relevant context when logging errors. Use structured key-value pairs.

```java
// Bad - minimal context
log.error("event=request_failed");

// Good - rich context
log.error("event=fetch_users_failed url={} status_code={} error={}",
    url, e.getStatus().getCode(), e.getStatus().getDescription());
```

## gRPC Error Mapping

Map gRPC status codes to domain exceptions using a clear mapping. Handle each code explicitly.

| gRPC Status Code | Domain Exception | Typical Meaning |
|---|---|---|
| `NOT_FOUND` | `ResourceNotFoundException` | Resource doesn't exist |
| `ALREADY_EXISTS` | `DuplicateResourceException` | Conflict on create |
| `INVALID_ARGUMENT` | `ValidationException` | Bad request data |
| `PERMISSION_DENIED` | `AccessDeniedException` | No permission |
| `UNAVAILABLE` | `ServiceUnavailableException` | Downstream is down |
| `DEADLINE_EXCEEDED` | `TimeoutException` | Call timed out |

```java
// Good - explicit mapping in a utility method
public static RuntimeException mapGrpcError(StatusRuntimeException e) {
    return switch (e.getStatus().getCode()) {
        case NOT_FOUND -> new ResourceNotFoundException(e.getStatus().getDescription());
        case ALREADY_EXISTS -> new DuplicateResourceException(e.getStatus().getDescription());
        case INVALID_ARGUMENT -> new ValidationException(e.getStatus().getDescription());
        case PERMISSION_DENIED -> new AccessDeniedException(e.getStatus().getDescription());
        case UNAVAILABLE -> new ServiceUnavailableException(e.getStatus().getDescription());
        case DEADLINE_EXCEEDED -> new TimeoutException(e.getStatus().getDescription());
        default -> e;  // Unknown codes propagate as-is
    };
}
```
