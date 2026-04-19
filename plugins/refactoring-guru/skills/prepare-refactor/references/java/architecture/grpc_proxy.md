# gRPC Client Adapter Patterns

Patterns for implementing gRPC client adapters in Java. For overall architecture structure, see `hexagonal_ddd.md`.

## Adapter Structure

gRPC adapter implements an outbound port interface and handles all gRPC-specific concerns. The stub is created eagerly from the injected channel.

```java
// Bad - adapter creates its own channel (untestable, unmanaged lifecycle)
public class GrpcAgentAdapter implements AgentPort {
    private final AgentServiceGrpc.AgentServiceBlockingStub stub;

    public GrpcAgentAdapter(String host, int port) {
        var channel = ManagedChannelBuilder.forAddress(host, port)
            .usePlaintext()
            .build();
        this.stub = AgentServiceGrpc.newBlockingStub(channel);
    }
}

// Good - channel injected, stub created eagerly
public class GrpcAgentAdapter implements AgentPort {
    private final AgentServiceGrpc.AgentServiceBlockingStub stub;

    public GrpcAgentAdapter(ManagedChannel channel) {
        this.stub = AgentServiceGrpc.newBlockingStub(channel);
    }

    @Override
    public AgentResponse processMessage(String userId, String message, String sessionId) {
        var request = toProto(userId, message, sessionId);
        var response = stub.process(request);
        return fromProto(response);
    }
}
```

## Proto Conversion

Keep conversion logic in the adapter. Domain models stay clean -- no protobuf dependencies.

```java
// Bad - domain model depends on protobuf
public record BacklinkItem(String sourceUrl, String targetUrl, String anchor, int pageScore) {
    public static BacklinkItem fromProto(BacklinkProto proto) {
        return new BacklinkItem(proto.getSourceUrl(), proto.getTargetUrl(),
            proto.getAnchor(), proto.getPageScore());
    }
}

// Good - conversion stays in adapter, domain is clean
public class GrpcBacklinksAdapter implements BacklinksPort {
    private final BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;

    public GrpcBacklinksAdapter(ManagedChannel channel) {
        this.stub = BacklinksServiceGrpc.newBlockingStub(channel);
    }

    @Override
    public List<BacklinkItem> fetchBacklinks(String url, int limit) {
        var request = toProto(url, limit);
        var items = new ArrayList<BacklinkItem>();
        stub.listBacklinks(request).forEachRemaining(proto -> items.add(fromProto(proto)));
        return List.copyOf(items);
    }

    private BacklinksRequest toProto(String url, int limit) {
        return BacklinksRequest.newBuilder()
            .setTarget(url)
            .setLimit(limit)
            .addAllExportColumns(List.of("source_url", "target_url", "anchor"))
            .build();
    }

    private BacklinkItem fromProto(BacklinkProto proto) {
        return new BacklinkItem(
            proto.getSourceUrl(),
            proto.getTargetUrl(),
            proto.getAnchor(),
            proto.getPageScore()
        );
    }
}

// Domain model - no protobuf dependency
public record BacklinkItem(String sourceUrl, String targetUrl, String anchor, int pageScore) {}
```

## gRPC Error Mapping

Map `StatusRuntimeException` codes to domain exceptions using a switch expression.

```java
// Bad - inline status checks scattered everywhere
public Optional<User> fetchUser(int userId) {
    try {
        return Optional.of(fromProto(stub.getUser(buildRequest(userId))));
    } catch (StatusRuntimeException e) {
        if (e.getStatus().getCode() == Status.Code.NOT_FOUND) {
            return Optional.empty();
        } else if (e.getStatus().getCode() == Status.Code.UNAVAILABLE) {
            throw new ServiceUnavailableException(e.getStatus().getDescription());
        } else if (e.getStatus().getCode() == Status.Code.DEADLINE_EXCEEDED) {
            throw new TimeoutException(e.getStatus().getDescription());
        }
        throw e;
    }
}

// Good - centralized mapping utility
public final class GrpcErrors {

    private GrpcErrors() {}

    public static RuntimeException mapToDomain(StatusRuntimeException e) {
        return switch (e.getStatus().getCode()) {
            case NOT_FOUND -> new ResourceNotFoundException(e.getStatus().getDescription());
            case INVALID_ARGUMENT -> new ValidationException(e.getStatus().getDescription());
            case UNAVAILABLE -> new ServiceUnavailableException(e.getStatus().getDescription());
            case DEADLINE_EXCEEDED -> new TimeoutException(e.getStatus().getDescription());
            case PERMISSION_DENIED -> new AccessDeniedException(e.getStatus().getDescription());
            case ALREADY_EXISTS -> new DuplicateResourceException(e.getStatus().getDescription());
            default -> e;
        };
    }
}

// Usage in adapter
@Override
public List<BacklinkItem> fetchBacklinks(String url, int limit) {
    try {
        var request = toProto(url, limit);
        var items = new ArrayList<BacklinkItem>();
        stub.listBacklinks(request).forEachRemaining(proto -> items.add(fromProto(proto)));
        return List.copyOf(items);
    } catch (StatusRuntimeException e) {
        throw GrpcErrors.mapToDomain(e);
    }
}
```

## Interceptor-Based Error Handling

Use `ClientInterceptor` for cross-cutting concerns like logging and error mapping. This is the Java equivalent of Python decorators.

```java
// Bad - repeated try/catch logging in every adapter method
public class GrpcBacklinksAdapter implements BacklinksPort {
    @Override
    public List<BacklinkItem> fetchBacklinks(String url, int limit) {
        try {
            return doFetch(url, limit);
        } catch (StatusRuntimeException e) {
            log.warn("event=fetch_backlinks_grpc_error code={} details={}",
                e.getStatus().getCode(), e.getStatus().getDescription());
            throw GrpcErrors.mapToDomain(e);
        }
    }

    @Override
    public BacklinksOverview fetchOverview(String url) {
        try {
            return doFetchOverview(url);
        } catch (StatusRuntimeException e) {
            log.warn("event=fetch_overview_grpc_error code={} details={}",
                e.getStatus().getCode(), e.getStatus().getDescription());
            throw GrpcErrors.mapToDomain(e);
        }
    }
}

// Good - interceptor handles logging and error mapping centrally
public class GrpcLoggingInterceptor implements ClientInterceptor {
    private static final Logger log = LoggerFactory.getLogger(GrpcLoggingInterceptor.class);

    @Override
    public <Req, Resp> ClientCall<Req, Resp> interceptCall(
            MethodDescriptor<Req, Resp> method, CallOptions options, Channel next) {
        return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, options)) {
            @Override
            public void start(Listener<Resp> responseListener, Metadata headers) {
                var wrappedListener = new ForwardingClientCallListener
                        .SimpleForwardingClientCallListener<Resp>(responseListener) {
                    @Override
                    public void onClose(Status status, Metadata trailers) {
                        if (!status.isOk()) {
                            log.warn("event=grpc_call_failed method={} code={} description={}",
                                method.getFullMethodName(), status.getCode(), status.getDescription());
                        }
                        super.onClose(status, trailers);
                    }
                };
                super.start(wrappedListener, headers);
            }
        };
    }
}

// Adapter stays clean
public class GrpcBacklinksAdapter implements BacklinksPort {
    private final BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;

    public GrpcBacklinksAdapter(ManagedChannel channel) {
        this.stub = BacklinksServiceGrpc.newBlockingStub(channel);
    }

    @Override
    public List<BacklinkItem> fetchBacklinks(String url, int limit) {
        var request = toProto(url, limit);
        var items = new ArrayList<BacklinkItem>();
        stub.listBacklinks(request).forEachRemaining(proto -> items.add(fromProto(proto)));
        return List.copyOf(items);
    }
}

// Interceptor attached during channel creation
var channel = ManagedChannelBuilder.forTarget(target)
    .intercept(new GrpcLoggingInterceptor())
    .build();
```

## Streaming Responses

Use `Iterator` from blocking stub or `StreamObserver` from async stub. Convert to domain models with streams.

```java
// Bad - manual iteration with mutable accumulator
public List<BacklinkItem> fetchBacklinks(String url, int limit) {
    var request = toProto(url, limit);
    Iterator<BacklinkProto> iterator = stub.listBacklinks(request);
    List<BacklinkItem> result = new ArrayList<>();
    while (iterator.hasNext()) {
        BacklinkProto proto = iterator.next();
        BacklinkItem item = fromProto(proto);
        result.add(item);
    }
    return result;
}

// Good - stream conversion with Spliterators
public List<BacklinkItem> fetchBacklinks(String url, int limit) {
    var request = toProto(url, limit);
    var iterator = stub.listBacklinks(request);
    return StreamSupport.stream(
            Spliterators.spliteratorUnknownSize(iterator, Spliterator.ORDERED), false)
        .map(this::fromProto)
        .toList();
}

// Good - async stub with StreamObserver for non-blocking streaming
public CompletableFuture<List<BacklinkItem>> fetchBacklinksAsync(String url, int limit) {
    var request = toProto(url, limit);
    var future = new CompletableFuture<List<BacklinkItem>>();
    var items = new ArrayList<BacklinkItem>();

    asyncStub.listBacklinks(request, new StreamObserver<>() {
        @Override
        public void onNext(BacklinkProto proto) {
            items.add(fromProto(proto));
        }

        @Override
        public void onError(Throwable t) {
            future.completeExceptionally(t);
        }

        @Override
        public void onCompleted() {
            future.complete(List.copyOf(items));
        }
    });

    return future;
}
```

## Channel Management

Manage `ManagedChannel` lifecycle properly. Channels are heavyweight -- create once, share across adapters, shut down gracefully.

```java
// Bad - channel never shut down, resource leak
public class GrpcBacklinksAdapter implements BacklinksPort {
    private final BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;

    public GrpcBacklinksAdapter(String target) {
        var channel = ManagedChannelBuilder.forTarget(target).usePlaintext().build();
        this.stub = BacklinksServiceGrpc.newBlockingStub(channel);
    }
    // channel leaked -- no way to shut it down
}

// Good - channel created externally, shutdown managed by owner
public class GrpcChannelManager {
    private final ManagedChannel channel;

    public GrpcChannelManager(String target) {
        this.channel = ManagedChannelBuilder.forTarget(target)
            .keepAliveTime(30, TimeUnit.SECONDS)
            .keepAliveTimeout(10, TimeUnit.SECONDS)
            .build();
    }

    public GrpcChannelManager(String target, long keepAliveSeconds, long keepAliveTimeoutSeconds) {
        this.channel = ManagedChannelBuilder.forTarget(target)
            .keepAliveTime(keepAliveSeconds, TimeUnit.SECONDS)
            .keepAliveTimeout(keepAliveTimeoutSeconds, TimeUnit.SECONDS)
            .build();
    }

    public ManagedChannel channel() {
        return channel;
    }

    public void shutdown() {
        channel.shutdown();
        try {
            if (!channel.awaitTermination(5, TimeUnit.SECONDS)) {
                channel.shutdownNow();
            }
        } catch (InterruptedException e) {
            channel.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}
```

## Channel as Dependency

Inject the channel via Spring `@Bean` configuration. Multiple adapters share the same channel.

```java
// Bad - each adapter creates its own channel
@Configuration
public class GrpcConfig {
    @Bean
    public GrpcBacklinksAdapter backlinksAdapter() {
        var channel = ManagedChannelBuilder.forTarget("backlinks:50051").usePlaintext().build();
        return new GrpcBacklinksAdapter(channel);
    }

    @Bean
    public GrpcOverviewAdapter overviewAdapter() {
        var channel = ManagedChannelBuilder.forTarget("backlinks:50051").usePlaintext().build();
        return new GrpcOverviewAdapter(channel);
    }
}

// Good - shared channel, proper lifecycle
@Configuration
public class GrpcConfig {
    @Bean
    public ManagedChannel backlinksChannel(@Value("${grpc.backlinks.target}") String target) {
        return ManagedChannelBuilder.forTarget(target)
            .keepAliveTime(30, TimeUnit.SECONDS)
            .keepAliveTimeout(10, TimeUnit.SECONDS)
            .intercept(new GrpcLoggingInterceptor())
            .build();
    }

    @Bean
    public GrpcBacklinksAdapter backlinksAdapter(ManagedChannel backlinksChannel) {
        return new GrpcBacklinksAdapter(backlinksChannel);
    }

    @Bean
    public GrpcOverviewAdapter overviewAdapter(ManagedChannel backlinksChannel) {
        return new GrpcOverviewAdapter(backlinksChannel);
    }

    @PreDestroy
    public void shutdownChannels() {
        backlinksChannel.shutdown();
    }
}
```

## Timeouts

Always set deadlines with `withDeadlineAfter()`. Calls without deadlines can hang indefinitely.

```java
// Bad - no deadline, call can hang forever
public List<BacklinkItem> fetchBacklinks(String url, int limit) {
    var request = toProto(url, limit);
    var iterator = stub.listBacklinks(request);
    return StreamSupport.stream(
            Spliterators.spliteratorUnknownSize(iterator, Spliterator.ORDERED), false)
        .map(this::fromProto)
        .toList();
}

// Good - deadline set on every call
public class GrpcBacklinksAdapter implements BacklinksPort {
    private static final long DEFAULT_TIMEOUT_SECONDS = 30;

    private final BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;
    private final long timeoutSeconds;

    public GrpcBacklinksAdapter(ManagedChannel channel, long timeoutSeconds) {
        this.stub = BacklinksServiceGrpc.newBlockingStub(channel);
        this.timeoutSeconds = timeoutSeconds;
    }

    public GrpcBacklinksAdapter(ManagedChannel channel) {
        this(channel, DEFAULT_TIMEOUT_SECONDS);
    }

    @Override
    public List<BacklinkItem> fetchBacklinks(String url, int limit) {
        var request = toProto(url, limit);
        var iterator = stub
            .withDeadlineAfter(timeoutSeconds, TimeUnit.SECONDS)
            .listBacklinks(request);
        return StreamSupport.stream(
                Spliterators.spliteratorUnknownSize(iterator, Spliterator.ORDERED), false)
            .map(this::fromProto)
            .toList();
    }
}
```

## Metadata/Headers

Pass metadata for tracing and authentication via interceptors. This keeps individual calls clean.

```java
// Bad - metadata added manually on every call
public List<BacklinkItem> fetchBacklinks(String url, int limit, String requestId, String token) {
    var request = toProto(url, limit);
    var metadata = new Metadata();
    metadata.put(Metadata.Key.of("x-request-id", Metadata.ASCII_STRING_MARSHALLER), requestId);
    metadata.put(Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER), "Bearer " + token);
    var callOptions = stub.getCallOptions();
    // ... awkward manual attachment
}

// Good - interceptor attaches metadata to all calls
public class AuthMetadataInterceptor implements ClientInterceptor {
    private final Supplier<String> tokenSupplier;

    public AuthMetadataInterceptor(Supplier<String> tokenSupplier) {
        this.tokenSupplier = tokenSupplier;
    }

    @Override
    public <Req, Resp> ClientCall<Req, Resp> interceptCall(
            MethodDescriptor<Req, Resp> method, CallOptions options, Channel next) {
        return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, options)) {
            @Override
            public void start(Listener<Resp> responseListener, Metadata headers) {
                headers.put(
                    Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER),
                    "Bearer " + tokenSupplier.get());
                super.start(responseListener, headers);
            }
        };
    }
}

// Good - tracing interceptor adds request-id
public class TracingMetadataInterceptor implements ClientInterceptor {
    private static final Metadata.Key<String> REQUEST_ID_KEY =
        Metadata.Key.of("x-request-id", Metadata.ASCII_STRING_MARSHALLER);

    @Override
    public <Req, Resp> ClientCall<Req, Resp> interceptCall(
            MethodDescriptor<Req, Resp> method, CallOptions options, Channel next) {
        return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, options)) {
            @Override
            public void start(Listener<Resp> responseListener, Metadata headers) {
                headers.put(REQUEST_ID_KEY, MDC.get("request_id"));
                super.start(responseListener, headers);
            }
        };
    }
}

// Attach interceptors during channel creation
var channel = ManagedChannelBuilder.forTarget(target)
    .intercept(
        new AuthMetadataInterceptor(tokenProvider::token),
        new TracingMetadataInterceptor(),
        new GrpcLoggingInterceptor())
    .build();
```

## Testing with Mock Stub

Mock the stub for unit tests. Inject it directly or use a mock channel.

```java
// Good - mock stub directly
@ExtendWith(MockitoExtension.class)
class GrpcBacklinksAdapterTest {

    @Mock
    private BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;

    private GrpcBacklinksAdapter adapter;

    @BeforeEach
    void setUp() {
        adapter = new GrpcBacklinksAdapter(stub);
    }

    @Test
    void fetchBacklinks_convertsProtosToDomain() {
        var proto1 = BacklinkProto.newBuilder()
            .setSourceUrl("http://a.com").setPageScore(50).build();
        var proto2 = BacklinkProto.newBuilder()
            .setSourceUrl("http://b.com").setPageScore(30).build();
        when(stub.listBacklinks(any())).thenReturn(List.of(proto1, proto2).iterator());

        var result = adapter.fetchBacklinks("example.com", 10);

        assertThat(result).hasSize(2);
        assertThat(result.get(0).sourceUrl()).isEqualTo("http://a.com");
        assertThat(result.get(1).pageScore()).isEqualTo(30);
    }

    @Test
    void fetchBacklinks_mapsNotFoundToEmpty() {
        when(stub.listBacklinks(any()))
            .thenThrow(new StatusRuntimeException(Status.NOT_FOUND));

        assertThatThrownBy(() -> adapter.fetchBacklinks("missing.com", 10))
            .isInstanceOf(ResourceNotFoundException.class);
    }
}
```

To allow injecting a stub directly for tests, add a package-private constructor:

```java
public class GrpcBacklinksAdapter implements BacklinksPort {
    private final BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;
    private final long timeoutSeconds;

    // Public - production use
    public GrpcBacklinksAdapter(ManagedChannel channel, long timeoutSeconds) {
        this.stub = BacklinksServiceGrpc.newBlockingStub(channel);
        this.timeoutSeconds = timeoutSeconds;
    }

    public GrpcBacklinksAdapter(ManagedChannel channel) {
        this(channel, 30);
    }

    // Package-private - test use
    GrpcBacklinksAdapter(BacklinksServiceGrpc.BacklinksServiceBlockingStub stub) {
        this.stub = stub;
        this.timeoutSeconds = 30;
    }
}
```
