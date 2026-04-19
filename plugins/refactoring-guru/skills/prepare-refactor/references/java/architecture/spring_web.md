# Spring Boot Web Service Patterns

Patterns for implementing REST API controllers with Spring Boot.

## Prefer WebFlux Over Spring MVC

Use the reactive stack (WebFlux) by default. It handles more concurrent connections with fewer threads and composes naturally with reactive clients (WebClient, reactive gRPC, R2DBC).

```java
// Bad - blocking MVC stack
@GetMapping
public BacklinksResponse backlinks(@RequestParam String url) {
    return service.backlinks(url);  // Blocks a platform thread
}

// Good - reactive stack
@GetMapping
public Mono<BacklinksResponse> backlinks(@RequestParam String url) {
    return service.backlinks(url);  // Non-blocking, thread released immediately
}
```

When to use MVC instead:
- Legacy codebase already on MVC with no migration path
- Heavy use of blocking libraries with no reactive alternatives (rare)

Key dependency: `spring-boot-starter-webflux` instead of `spring-boot-starter-web`.

## Thin Controllers Pattern

Controllers are thin HTTP handlers that delegate to services. NO business logic in controllers. Return reactive types (`Mono`/`Flux`).

```java
// Good - thin reactive controller, delegates to service
@RestController
@RequestMapping("/backlinks")
public class BacklinksController {
    private final BacklinksService service;

    public BacklinksController(BacklinksService service) {
        this.service = service;
    }

    @GetMapping
    public Mono<BacklinksResponse> backlinks(@RequestParam String url, @RequestParam(defaultValue = "10") int limit) {
        return service.backlinks(url, limit);
    }

    @GetMapping("/stream")
    public Flux<BacklinkItem> stream(@RequestParam String url) {
        return service.streamBacklinks(url);
    }
}
```

```java
// Bad - business logic in controller
@RestController
@RequestMapping("/backlinks")
public class BacklinksController {
    private final BacklinksGrpcClient client;

    public BacklinksController(BacklinksGrpcClient client) {
        this.client = client;
    }

    @GetMapping
    public Mono<BacklinksResponse> backlinks(@RequestParam String url) {
        return Mono.fromCallable(() -> {
            var validatedUrl = UrlValidator.validate(url);   // Logic!
            var request = BasicRequest.newBuilder()
                .setTarget(validatedUrl)
                .setLimit(10)
                .build();                                     // Building protos!
            var items = new ArrayList<BacklinkItem>();
            client.fetch(request).forEachRemaining(
                item -> items.add(convertItem(item)));        // Conversion logic!
            return new BacklinksResponse(items);
        });
    }
}
```

## Constructor Injection

Spring auto-discovers a single constructor. No `@Autowired` needed. When a class has exactly one constructor, Spring uses it for injection automatically.

```java
// Bad - field injection (hides dependencies, untestable without reflection)
@RestController
public class UserController {
    @Autowired
    private UserService userService;
    @Autowired
    private AuditService auditService;
}

// Bad - unnecessary @Autowired on single constructor
@RestController
public class UserController {
    private final UserService userService;

    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }
}

// Good - single constructor, Spring injects automatically
@RestController
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/users/{id}")
    public Mono<UserResponse> user(@PathVariable int id) {
        return userService.user(id);
    }
}
```

Multiple dependencies work the same way:

```java
@RestController
@RequestMapping("/reports")
public class ReportController {
    private final ReportService reportService;
    private final ExportService exportService;

    public ReportController(ReportService reportService, ExportService exportService) {
        this.reportService = reportService;
        this.exportService = exportService;
    }
}
```

## Testing with WebTestClient

Use `@WebFluxTest` for controller slice tests. It loads only the web layer, not the full application context. Use `@MockBean` to replace service dependencies. `WebTestClient` is the reactive equivalent of `MockMvc`.

```java
@WebFluxTest(BacklinksController.class)
class BacklinksControllerTest {
    @Autowired
    private WebTestClient webClient;

    @MockBean
    private BacklinksService service;

    @Test
    void backlinksReturnsItems() {
        var response = new BacklinksResponse(List.of(
            new BacklinkItem("https://source.com", "https://target.com", "click here", 85)
        ));
        when(service.backlinks("example.com", 10)).thenReturn(Mono.just(response));

        webClient.get().uri("/backlinks?url=example.com&limit=10")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.items[0].sourceUrl").isEqualTo("https://source.com")
            .jsonPath("$.items[0].pageScore").isEqualTo(85);
    }

    @Test
    void backlinksReturnsBadRequestWhenUrlMissing() {
        webClient.get().uri("/backlinks")
            .exchange()
            .expectStatus().isBadRequest();
    }
}
```

For testing service logic directly, skip Spring entirely and pass mocks through the constructor. Use `StepVerifier` to test reactive pipelines:

```java
class BacklinksServiceTest {
    private final BacklinksPort backlinksPort = mock(BacklinksPort.class);
    private final BacklinksService service = new BacklinksService(backlinksPort);

    @Test
    void backlinksReturnsConvertedItems() {
        when(backlinksPort.fetch("example.com", 10))
            .thenReturn(Flux.just(new Backlink("https://source.com", "click here", 85)));

        StepVerifier.create(service.backlinks("example.com", 10))
            .assertNext(response -> {
                assertThat(response.items()).hasSize(1);
                assertThat(response.items().getFirst().anchor()).isEqualTo("click here");
            })
            .verifyComplete();
    }
}
```

## Records for Request/Response DTOs

Use records for request and response objects. Add Jakarta validation annotations directly on record components.

```java
// Response DTOs
public record BacklinkItem(String sourceUrl, String targetUrl, String anchor, int pageScore) {}

public record BacklinksResponse(List<BacklinkItem> items) {}

// Request DTOs with validation
public record BacklinksRequest(
    @NotBlank String url,
    @Min(1) @Max(100) int limit,
    @Pattern(regexp = "asc|desc") String sortDirection
) {
    // Compact constructor for defaults
    public BacklinksRequest {
        if (sortDirection == null) {
            sortDirection = "desc";
        }
    }
}

// Nested records work well for structured responses
public record SearchResponse(
    List<SearchHit> hits,
    int totalCount,
    SearchMeta meta
) {
    public record SearchHit(String url, String title, double score) {}
    public record SearchMeta(long queryTimeMs, String index) {}
}
```

```java
// Bad - mutable POJO with setters
public class BacklinksRequest {
    private String url;
    private int limit;

    public void setUrl(String url) { this.url = url; }
    public void setLimit(int limit) { this.limit = limit; }
    public String getUrl() { return url; }
    public int getLimit() { return limit; }
}
```

## Request Validation

Use `@Valid` on request bodies and Jakarta annotations on record components. Use `@RequestParam` with `defaultValue` for query parameters.

```java
// Query parameter validation with defaults
@GetMapping("/search")
public Mono<SearchResponse> search(
        @RequestParam @Size(min = 1, max = 200) String query,
        @RequestParam(defaultValue = "10") @Min(1) @Max(100) int limit,
        @RequestParam(defaultValue = "0") @Min(0) int offset,
        @RequestParam(defaultValue = "relevance") String sort) {
    return searchService.search(query, limit, offset, sort);
}

// Request body validation with @Valid
@PostMapping("/domains/analyze")
public Mono<AnalysisResponse> analyze(@Valid @RequestBody AnalysisRequest request) {
    return analysisService.analyze(request);
}
```

```java
// Record with Jakarta validation
public record AnalysisRequest(
    @NotBlank @Size(max = 253) String domain,
    @NotNull AnalysisType type,
    @Min(1) @Max(1000) int depth
) {}

// Custom validation with compact constructor
public record DateRangeRequest(
    @NotNull LocalDate from,
    @NotNull LocalDate to
) {
    public DateRangeRequest {
        if (from.isAfter(to)) {
            throw new IllegalArgumentException("'from' must not be after 'to'");
        }
    }
}
```

## Exception Handlers with @ControllerAdvice

Register a global exception handler to convert domain exceptions to HTTP responses. Controllers stay clean.

```java
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException e) {
        return ResponseEntity.status(404).body(new ErrorResponse(e.getMessage()));
    }

    @ExceptionHandler(DomainValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidation(DomainValidationException e) {
        return ResponseEntity.status(422).body(new ErrorResponse(e.getMessage()));
    }

    @ExceptionHandler(QuotaExceededException.class)
    public ResponseEntity<ErrorResponse> handleQuota(QuotaExceededException e) {
        return ResponseEntity.status(429).body(new ErrorResponse(e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleBeanValidation(MethodArgumentNotValidException e) {
        var message = e.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest().body(new ErrorResponse(message));
    }
}

public record ErrorResponse(String detail) {}
```

Domain exceptions are simple, focused classes:

```java
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}

public class QuotaExceededException extends RuntimeException {
    private final String domain;
    private final int limit;

    public QuotaExceededException(String domain, int limit) {
        super("Quota exceeded for %s (limit: %d)".formatted(domain, limit));
        this.domain = domain;
        this.limit = limit;
    }

    public String domain() { return domain; }
    public int limit() { return limit; }
}
```

Controllers throw domain exceptions, `@ControllerAdvice` maps them to HTTP:

```java
// Service throws domain exception
@Service
public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }

    public Mono<UserResponse> user(int id) {
        return repository.findById(id)
            .map(u -> new UserResponse(u.name(), u.email()))
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("User not found: " + id)));
    }
}

// Controller stays thin - no try/catch
@RestController
@RequestMapping("/users")
public class UserController {
    private final UserService service;

    public UserController(UserService service) {
        this.service = service;
    }

    @GetMapping("/{id}")
    public Mono<UserResponse> user(@PathVariable int id) {
        return service.user(id);
    }
}
```

## Controller Organization

Group controllers by domain. Use `@RequestMapping` at class level for the common prefix.

```java
// backlinks/BacklinksController.java
@RestController
@RequestMapping("/backlinks")
public class BacklinksController {
    private final BacklinksService service;

    public BacklinksController(BacklinksService service) {
        this.service = service;
    }

    @GetMapping
    public Mono<BacklinksResponse> list(@RequestParam String url, @RequestParam(defaultValue = "10") int limit) {
        return service.backlinks(url, limit);
    }

    @GetMapping("/overview")
    public Mono<OverviewResponse> overview(@RequestParam String url) {
        return service.overview(url);
    }
}

// health/HealthController.java
@RestController
public class HealthController {

    @GetMapping("/health")
    public Mono<Map<String, String>> health() {
        return Mono.just(Map.of("status", "ok"));
    }
}
```

For larger services, organize controllers into packages by domain:

```
adapters/inbound/rest/
    backlinks/
        BacklinksController.java
        BacklinksRequest.java
        BacklinksResponse.java
    users/
        UserController.java
        UserResponse.java
    health/
        HealthController.java
    GlobalExceptionHandler.java
```

## Application Lifecycle

Use `@PostConstruct`/`@PreDestroy` for bean-level lifecycle, `ApplicationRunner` for startup tasks, and `DisposableBean` or `@PreDestroy` for shutdown cleanup.

### Bean Lifecycle

```java
@Component
public class CacheWarmer {
    private final CacheService cacheService;

    public CacheWarmer(CacheService cacheService) {
        this.cacheService = cacheService;
    }

    @PostConstruct
    void warmCache() {
        cacheService.loadFrequentEntries();
    }

    @PreDestroy
    void flushCache() {
        cacheService.flush();
    }
}
```

### Startup Tasks with ApplicationRunner

Use `ApplicationRunner` for tasks that run once after the full application context is ready.

```java
@Component
public class MigrationRunner implements ApplicationRunner {
    private final MigrationService migrationService;

    public MigrationRunner(MigrationService migrationService) {
        this.migrationService = migrationService;
    }

    @Override
    public void run(ApplicationArguments args) {
        migrationService.runPendingMigrations();
    }
}
```

### Graceful Shutdown

```java
@Component
public class GrpcChannelManager {
    private final ManagedChannel channel;

    public GrpcChannelManager(ManagedChannel channel) {
        this.channel = channel;
    }

    @PreDestroy
    void shutdown() {
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

### Anti-Pattern: Lazy Initialization in Beans

```java
// Bad - lazy init with mutable state
@Component
public class BacklinksAdapter {
    private BacklinksStub stub;  // null until first use

    public Flux<Backlink> fetch(String url) {
        if (stub == null) {           // Mutable! Race condition!
            stub = createStub();
        }
        return stub.fetch(url);
    }
}

// Good - eager init in constructor
@Component
public class BacklinksAdapter {
    private final BacklinksStub stub;

    public BacklinksAdapter(ManagedChannel channel) {
        this.stub = ReactorBacklinksGrpc.newReactorStub(channel);
    }

    public Flux<Backlink> fetch(String url) {
        return stub.fetch(buildRequest(url));
    }
}
```

## Configuration with @ConfigurationProperties

Use `@ConfigurationProperties` with records for type-safe, immutable configuration bound from `application.yml` or environment variables.

```java
@ConfigurationProperties(prefix = "app.api")
public record ApiProperties(
    String host,
    int port,
    Duration timeout,
    int maxRetries
) {
    // Compact constructor for defaults
    public ApiProperties {
        if (host == null) host = "0.0.0.0";
        if (port == 0) port = 8080;
        if (timeout == null) timeout = Duration.ofSeconds(30);
        if (maxRetries == 0) maxRetries = 3;
    }
}
```

Enable it on the application class or a configuration class:

```java
@SpringBootApplication
@ConfigurationPropertiesScan
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

Inject properties via constructor, just like any other dependency:

```java
@Service
public class BacklinksService {
    private final BacklinksPort backlinksPort;
    private final int maxRetries;

    public BacklinksService(BacklinksPort backlinksPort, ApiProperties properties) {
        this.backlinksPort = backlinksPort;
        this.maxRetries = properties.maxRetries();
    }
}
```

### Split Configuration by Environment

Split `application.yml` into separate profile-specific files. The base file holds shared defaults, profile files override per environment.

```
src/main/resources/
├── application.yml              # Shared defaults
├── application-dev.yml          # Local development
├── application-rc.yml           # Release candidate / staging
└── application-prod.yml         # Production
```

**`application.yml`** — shared defaults, never environment-specific:

```yaml
app:
  api:
    timeout: 30s
    max-retries: 3
```

**`application-dev.yml`** — local development overrides:

```yaml
app:
  api:
    host: localhost
    port: 8080

logging:
  level:
    root: DEBUG
```

**`application-rc.yml`** — staging:

```yaml
app:
  api:
    host: 0.0.0.0
    port: 8080
    max-retries: 5

logging:
  level:
    root: INFO
```

**`application-prod.yml`** — production:

```yaml
app:
  api:
    host: 0.0.0.0
    port: 8080
    timeout: 10s
    max-retries: 10

logging:
  level:
    root: WARN
```

Activate a profile at runtime:

```bash
java -jar app.jar --spring.profiles.active=prod
# or via environment variable
SPRING_PROFILES_ACTIVE=rc java -jar app.jar
```

```java
// Bad - all environments in one file with conditional logic
// Bad - environment-specific values hardcoded in code
// Bad - a single massive application.yml with spring.config.activate.on-profile blocks
```

```java
// Bad - @Value scattered across classes
@Service
public class BacklinksService {
    @Value("${app.api.host}")
    private String host;
    @Value("${app.api.timeout}")
    private Duration timeout;
    @Value("${app.api.max-retries}")
    private int maxRetries;
}

// Bad - mutable properties class with setters
@ConfigurationProperties(prefix = "app.api")
public class ApiProperties {
    private String host;
    private int port;

    public void setHost(String host) { this.host = host; }
    public void setPort(int port) { this.port = port; }
    public String getHost() { return host; }
    public int getPort() { return port; }
}
```
