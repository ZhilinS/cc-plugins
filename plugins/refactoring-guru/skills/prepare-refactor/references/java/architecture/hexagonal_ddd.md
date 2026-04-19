# Hexagonal Architecture with DDD (Ports & Adapters)

A clean architecture pattern that separates domain logic from infrastructure concerns, implemented with Java and Spring Boot.

## Directory Structure

```
service/
├── src/main/java/com/semrush/service/
│   ├── core/                              # Domain logic, minimal external deps
│   │   ├── domain/
│   │   │   ├── model/                     # Records, value objects
│   │   │   │   ├── BacklinksData.java
│   │   │   │   ├── Analysis.java
│   │   │   │   └── UrlScope.java
│   │   │   └── exception/                 # Domain-specific exceptions
│   │   │       ├── DomainException.java
│   │   │       ├── ValidationException.java
│   │   │       └── NotFoundException.java
│   │   │
│   │   ├── application/                   # Business logic orchestration
│   │   │   ├── BacklinksAnalysisService.java
│   │   │   ├── MessageService.java
│   │   │   └── validators/
│   │   │       └── MessageValidator.java
│   │   │
│   │   └── port/
│   │       ├── inbound/                   # How outside world calls us
│   │       │   └── AnalyzeBacklinksUseCase.java
│   │       └── outbound/                  # How we call outside world
│   │           ├── BacklinksPort.java
│   │           ├── DialoguePort.java
│   │           └── SessionPort.java
│   │
│   ├── adapter/                           # Implementations of ports
│   │   ├── inbound/
│   │   │   └── rest/                      # Spring REST controllers
│   │   │       └── BacklinksController.java
│   │   └── outbound/
│   │       ├── grpc/                      # gRPC adapters
│   │       │   └── BacklinksGrpcAdapter.java
│   │       └── persistence/               # Database adapters
│   │           └── DialogueJdbcAdapter.java
│   │
│   └── config/                            # Spring @Configuration wiring
│       └── ApplicationConfig.java
│
└── src/test/java/
    ├── unit/
    └── integration/
```

## Architecture Flow Diagrams

### Dependency Direction

**CRITICAL: Dependencies point INWARD toward the domain. The domain never depends on adapters.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL WORLD                                   │
│                                                                             │
│   HTTP Request    gRPC Request    Database    Redis    Message Queue       │
│        │               │              ▲          ▲           ▲              │
└────────┼───────────────┼──────────────┼──────────┼───────────┼──────────────┘
         │               │              │          │           │
         ▼               ▼              │          │           │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ADAPTERS LAYER                                     │
│                                                                             │
│   ┌─────────────────────┐              ┌─────────────────────────────────┐ │
│   │   INBOUND ADAPTERS  │              │      OUTBOUND ADAPTERS          │ │
│   │                     │              │                                 │ │
│   │  @RestController    │              │  @Component                     │ │
│   │  @GrpcService       │              │  DialogueJdbcAdapter            │ │
│   │  @KafkaListener     │              │    implements DialoguePort      │ │
│   │                     │              │  BacklinksGrpcAdapter           │ │
│   │  Calls ──────────┐  │              │    implements BacklinksPort     │ │
│   └──────────────────┼──┘              └────────────────────────────┼───┘ │
│                      │                                               │     │
└──────────────────────┼───────────────────────────────────────────────┼─────┘
                       │                                               │
                       ▼                                               │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOMAIN LAYER                                      │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                      APPLICATION (Services)                          │ │
│   │                                                                      │ │
│   │   @Service                                                           │ │
│   │   class BacklinksAnalysisService {                                   │ │
│   │       private final BacklinksPort backlinks;  ◄──────────────────────┼─┤
│   │                                               // depends on PORT     │ │
│   │       Analysis analyze(String url) {                                 │ │
│   │           var data = backlinks.fetchData(url);  // calls PORT        │ │
│   │           return applyBusinessLogic(data);                           │ │
│   │       }                                                              │ │
│   │   }                                                                  │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              │ uses                                         │
│                              ▼                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                         PORTS (Interfaces)                           │ │
│   │                                                                      │ │
│   │   interface BacklinksPort {          interface DialoguePort {         │ │
│   │       BacklinksData fetchData(url)       String ensureActive(userId)  │ │
│   │   }                                 }                                │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                              ▲                                              │
│                              │                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                    DOMAIN MODELS (Records)                           │ │
│   │                                                                      │ │
│   │   record BacklinksData(             // Pure Java preferred            │ │
│   │       int total,                    // Jackson/generated enums OK    │ │
│   │       double score                  // no JPA, no protobuf messages  │ │
│   │   ) {}                                                               │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow: Who Calls Whom

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ INBOUND ADAPTER (Spring Controller)                                         │
│                                                                             │
│   @RestController                                                           │
│   class BacklinksController {                                               │
│       private final BacklinksAnalysisService service;                       │
│                                                                             │
│       @PostMapping("/backlinks")                                            │
│       Analysis analyzeBacklinks(@RequestBody AnalyzeRequest request) {     │
│           return service.analyze(request.url()); // CALLS service           │
│       }                                          ─────────┐                 │
│   }                                                        │                │
└────────────────────────────────────────────────────────────┼────────────────┘
                                                             │
                                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ DOMAIN SERVICE (Business Logic)                                             │
│                                                                             │
│   @Service                                                                  │
│   class BacklinksAnalysisService {                                          │
│       private final BacklinksPort backlinks;  // depends on PORT            │
│                                                                             │
│       BacklinksAnalysisService(BacklinksPort backlinks) {                   │
│           this.backlinks = backlinks;                                       │
│       }                                                                     │
│                                                                             │
│       Analysis analyze(String url) {                                        │
│           var data = backlinks.fetchData(url);  // CALLS port               │
│           var risk = calculateRisk(data);        // business logic          │
│           return new Analysis(data, risk);       ──────┐                    │
│       }                                                 │                   │
│   }                                                     │                   │
└─────────────────────────────────────────────────────────┼───────────────────┘
                                                          │
                              Port interface              │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTBOUND ADAPTER (Implements Port)                                          │
│                                                                             │
│   @Component                                                                │
│   class BacklinksGrpcAdapter implements BacklinksPort {                     │
│                                                                             │
│       BacklinksData fetchData(String url) {                                 │
│           // 1. Translate domain → protobuf                                 │
│           var request = toProto(url);                                       │
│           // 2. Call external system                                        │
│           var response = stub.getBacklinks(request);                        │
│           // 3. Translate protobuf → domain                                 │
│           return toDomain(response);                                        │
│       }                                                                     │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                      External gRPC Service
```

### Adapter Responsibilities: Translation Layer

**Adapters are the ONLY place where translation happens.** Domain models stay clean.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OUTBOUND ADAPTER                                     │
│                                                                             │
│   @Component                                                                │
│   class BacklinksGrpcAdapter implements BacklinksPort {                     │
│       /**                                                                   │
│        * Adapter responsibility: TRANSLATION between domain and infra       │
│        * - Domain objects ↔ Protobuf messages                               │
│        * - Domain exceptions ↔ gRPC status codes                            │
│        * - Domain types ↔ External API types                                │
│        */                                                                   │
│                                                                             │
│       private BacklinksRequest toProto(String url, UrlScope scope) {        │
│           // Domain → Protobuf translation                                  │
│           return BacklinksRequest.newBuilder()                               │
│               .setTarget(url)                                               │
│               .setTargetType(scopeToProto(scope))  // enum mapping          │
│               .build();                                                     │
│       }                                                                     │
│                                                                             │
│       private BacklinksData toDomain(BacklinksProto proto) {                │
│           // Protobuf → Domain translation                                  │
│           return new BacklinksData(                                          │
│               proto.getTotalBacklinks(),                                     │
│               proto.getAuthorityScore(),                                     │
│               proto.getRefdomainsList().stream()                             │
│                   .map(this::mapRefdomain)                                   │
│                   .toList()                                                  │
│           );                                                                │
│       }                                                                     │
│                                                                             │
│       public BacklinksData fetchData(String url, UrlScope scope) {          │
│           var request = toProto(url, scope);          // translate IN        │
│           var response = stub.summary(request);       // call external      │
│           return toDomain(response);                  // translate OUT       │
│       }                                                                     │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Common Mistake: Adapter Just Forwards (Wrong!)

```java
// Bad - Adapter does nothing, just forwards to service
@Component
class BacklinksAdapter implements BacklinksPort {
    private final BacklinksService service;

    BacklinksAdapter(BacklinksService service) {
        this.service = service;
    }

    @Override
    public BacklinksData fetchData(String url) {
        return service.fetchData(url);  // Just forwarding!
    }
}

// Bad - Service does translation (adapter's job)
@Service
class BacklinksService {
    private final BacklinksStub stub;

    BacklinksData fetchData(String url) {
        var request = BacklinksRequest.newBuilder()    // Protobuf in service!
            .setTarget(url)
            .build();
        var response = stub.getBacklinks(request);
        return new BacklinksData(response.getTotal()); // Translation here!
    }
}
```

**Why this is wrong:**
1. Adapter adds no value -- it is just a passthrough
2. Service is coupled to protobuf (infrastructure concern)
3. Dependency is inverted: adapter -> service instead of service -> port <- adapter

### Correct Pattern: Service Uses Port, Adapter Implements Port

```java
// Good - Service depends on Port (abstraction)
@Service
class BacklinksAnalysisService {
    private final BacklinksPort backlinks;  // Port, not adapter!

    BacklinksAnalysisService(BacklinksPort backlinks) {
        this.backlinks = backlinks;
    }

    Analysis analyze(String url) {
        var data = backlinks.fetchData(url);   // Calls port method
        var risk = calculateRisk(data);         // Business logic
        return new Analysis(data, risk);
    }
}

// Good - Adapter implements Port, does translation
@Component
class BacklinksGrpcAdapter implements BacklinksPort {
    private final BacklinksStub stub;

    BacklinksGrpcAdapter(BacklinksStub stub) {
        this.stub = stub;
    }

    @Override
    public BacklinksData fetchData(String url) {
        var request = toProto(url);                    // Translation
        var response = stub.getBacklinks(request);
        return toDomain(response);                     // Translation
    }
}
```

### When You Don't Need Separate Services

If your application has **no business logic** (just fetch, transform, return), you have two options:

**Option A: Adapter implements Port directly (no separate service)**

```
Controller -> Port -> Adapter (does translation + external call)
```

```java
// Adapter IS the implementation, no service layer needed
@Component
class BacklinksGrpcAdapter implements BacklinksPort {
    @Override
    public BacklinksData fetchData(String url) {
        // Translation + call - this IS the implementation
        ...
    }
}

// Controller uses port directly
@RestController
class BacklinksController {
    private final BacklinksPort backlinks;

    BacklinksController(BacklinksPort backlinks) {
        this.backlinks = backlinks;
    }

    @GetMapping("/backlinks")
    BacklinksData backlinks(@RequestParam String url) {
        return backlinks.fetchData(url);
    }
}
```

**Option B: Service implements Port (rename adapter to service)**

```
Controller -> Port -> Service (implements Port, does translation + external call)
```

```java
// Service implements Port directly
@Service
class BacklinksService implements BacklinksPort {
    @Override
    public BacklinksData fetchData(String url) {
        // Translation + call
        ...
    }
}
```

Both are valid when there is no domain logic. Choose based on naming preference.

## Layer Responsibilities

### Domain Layer (`core/domain/`)

Pure business entities with minimal dependencies on external systems. No JPA, no protobuf messages.

**Pragmatic exceptions** (do NOT flag these as violations):
- **Spring annotations** (`@Service`, `@Component`, etc.) in the core layer are acceptable -- Spring is the framework, not an external system.
- **Jackson annotations** (`@JsonProperty`, `@JsonIgnore`, etc.) on domain models are acceptable -- serialization is a cross-cutting concern and wrapping every model in a DTO just to avoid an annotation adds complexity without real benefit.
- **Generated enums** (e.g., jOOQ-generated DB enums, protobuf enums) used as domain values are acceptable -- these are stable value types and duplicating them into domain enums with mapping logic is overhead that rarely pays off.

```java
// core/domain/model/BacklinksData.java
public record BacklinksData(
    int total,
    double score,
    List<Refdomain> refdomains
) {
    public BacklinksData {
        refdomains = List.copyOf(refdomains);  // Defensive copy for immutability
    }
}
```

```java
// core/domain/model/Analysis.java
public record Analysis(
    BacklinksData data,
    RiskLevel risk
) {}
```

```java
// core/domain/model/UrlScope.java
public enum UrlScope {
    ROOT_DOMAIN,
    SUBDOMAIN,
    EXACT_URL
}
```

```java
// core/domain/exception/DomainException.java
public class DomainException extends RuntimeException {
    public DomainException(String message) {
        super(message);
    }

    public DomainException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

```java
// core/domain/exception/ValidationException.java
public class ValidationException extends DomainException {
    public ValidationException(String message) {
        super(message);
    }
}
```

```java
// core/domain/exception/NotFoundException.java
public class NotFoundException extends DomainException {
    public NotFoundException(String message) {
        super(message);
    }
}
```

### Ports Layer (`core/port/`)

Java interfaces that define contracts. No implementations.

**Outbound ports** -- interfaces for external dependencies (what the core needs from outside):

```java
// core/port/outbound/BacklinksPort.java

/**
 * Port for fetching backlinks data from an external source.
 *
 * <p>Implementations handle the specifics of communication
 * (gRPC, HTTP, database) and translate between domain models
 * and infrastructure types.
 */
public interface BacklinksPort {

    /**
     * Fetch backlinks data for a URL.
     *
     * @param url   the target URL
     * @param scope the analysis scope (root domain, subdomain, exact URL)
     * @return backlinks data in domain model form
     */
    BacklinksData fetchData(String url, UrlScope scope);

    /**
     * Fetch backlinks data with default scope (root domain).
     */
    default BacklinksData fetchData(String url) {
        return fetchData(url, UrlScope.ROOT_DOMAIN);
    }
}
```

```java
// core/port/outbound/DialoguePort.java

/**
 * Port for managing user dialogues.
 *
 * <p>Defines how the core application interacts with dialogue storage.
 */
public interface DialoguePort {

    /**
     * Get the active dialogue for a user or create a new one.
     *
     * @param userId the user identifier
     * @return the dialogue ID as a string (UUID format)
     */
    String ensureActive(long userId);

    /**
     * Find the active dialogue for a user if one exists.
     */
    Optional<String> findActive(long userId);

    /**
     * Soft delete the active dialogue for a user.
     *
     * @return number of deleted records
     */
    int softDelete(long userId);
}
```

**Inbound ports** -- interfaces for incoming requests (how outside calls the core):

```java
// core/port/inbound/AnalyzeBacklinksUseCase.java

/**
 * Use case for analyzing backlinks of a URL.
 */
public interface AnalyzeBacklinksUseCase {

    Analysis analyze(String url);

    Analysis analyze(String url, UrlScope scope);
}
```

### Application Layer (`core/application/`)

Orchestrates domain logic, uses ports for external interactions. This is where Spring's `@Service` annotation lives.

```java
// core/application/BacklinksAnalysisService.java

@Service
class BacklinksAnalysisService implements AnalyzeBacklinksUseCase {
    private final BacklinksPort backlinks;

    BacklinksAnalysisService(BacklinksPort backlinks) {
        this.backlinks = backlinks;
    }

    @Override
    public Analysis analyze(String url) {
        return analyze(url, UrlScope.ROOT_DOMAIN);
    }

    @Override
    public Analysis analyze(String url, UrlScope scope) {
        var data = backlinks.fetchData(url, scope);
        var risk = calculateRisk(data);
        return new Analysis(data, risk);
    }

    private RiskLevel calculateRisk(BacklinksData data) {
        if (data.score() < 20) return RiskLevel.HIGH;
        if (data.score() < 50) return RiskLevel.MEDIUM;
        return RiskLevel.LOW;
    }
}
```

```java
// core/application/MessageService.java

@Service
class MessageService {
    private final AgentPort agent;
    private final DialoguePort dialogue;
    private final SessionPort session;

    MessageService(AgentPort agent, DialoguePort dialogue, SessionPort session) {
        this.agent = agent;
        this.dialogue = dialogue;
        this.session = session;
    }

    MessageResponse processMessage(long userId, String message) {
        // Get or create dialogue
        var dialogueId = dialogue.ensureActive(userId);

        // Get or create session
        var sessionId = session.getOrCreate(userId, dialogueId);

        // Process through agent
        var response = agent.processMessage(
            String.valueOf(userId),
            message,
            sessionId,
            Map.of()
        );

        return new MessageResponse(response.content(), dialogueId);
    }
}
```

### Adapters Layer (`adapter/`)

Concrete implementations of ports.

**Outbound adapter** (implements port interface):

```java
// adapter/outbound/grpc/BacklinksGrpcAdapter.java

@Component
class BacklinksGrpcAdapter implements BacklinksPort {
    private final BacklinksServiceGrpc.BacklinksServiceBlockingStub stub;

    BacklinksGrpcAdapter(BacklinksServiceGrpc.BacklinksServiceBlockingStub stub) {
        this.stub = stub;
    }

    @Override
    public BacklinksData fetchData(String url, UrlScope scope) {
        var request = toProto(url, scope);
        var response = stub.summary(request);
        return toDomain(response);
    }

    private BacklinksRequest toProto(String url, UrlScope scope) {
        return BacklinksRequest.newBuilder()
            .setTarget(url)
            .setTargetType(scopeToProto(scope))
            .build();
    }

    private BacklinksData toDomain(BacklinksResponse response) {
        return new BacklinksData(
            response.getTotalBacklinks(),
            response.getAuthorityScore(),
            response.getRefdomainsList().stream()
                .map(this::mapRefdomain)
                .toList()
        );
    }

    private TargetType scopeToProto(UrlScope scope) {
        return switch (scope) {
            case ROOT_DOMAIN -> TargetType.ROOT_DOMAIN;
            case SUBDOMAIN -> TargetType.SUBDOMAIN;
            case EXACT_URL -> TargetType.URL;
        };
    }

    private Refdomain mapRefdomain(RefdomainProto proto) {
        return new Refdomain(proto.getDomain(), proto.getBacklinksCount());
    }
}
```

```java
// adapter/outbound/persistence/DialogueJdbcAdapter.java

@Component
class DialogueJdbcAdapter implements DialoguePort {
    private final JdbcTemplate jdbc;

    DialogueJdbcAdapter(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public String ensureActive(long userId) {
        return findActive(userId).orElseGet(() -> createNew(userId));
    }

    @Override
    public Optional<String> findActive(long userId) {
        var results = jdbc.queryForList(
            """
            SELECT dialogue_id FROM dialogue
            WHERE user_id = ? AND deleted = false
            ORDER BY created_at DESC LIMIT 1
            """,
            String.class,
            userId
        );
        return results.stream().findFirst();
    }

    @Override
    public int softDelete(long userId) {
        return jdbc.update(
            "UPDATE dialogue SET deleted = true WHERE user_id = ? AND deleted = false",
            userId
        );
    }

    private String createNew(long userId) {
        var id = UUID.randomUUID().toString();
        jdbc.update(
            "INSERT INTO dialogue (dialogue_id, user_id, created_at) VALUES (?, ?, ?)",
            id, userId, Instant.now()
        );
        return id;
    }
}
```

**Inbound adapter** (calls application layer):

```java
// adapter/inbound/rest/BacklinksController.java

@RestController
@RequestMapping("/backlinks")
class BacklinksController {
    private final AnalyzeBacklinksUseCase analyzeBacklinks;

    BacklinksController(AnalyzeBacklinksUseCase analyzeBacklinks) {
        this.analyzeBacklinks = analyzeBacklinks;
    }

    @PostMapping
    Analysis analyze(@RequestBody AnalyzeRequest request) {
        return analyzeBacklinks.analyze(request.url());
    }
}
```

### Configuration Layer (`config/`)

Spring `@Configuration` wires adapters to ports. This is the composition root.

```java
// config/ApplicationConfig.java

@Configuration
class ApplicationConfig {

    @Bean
    BacklinksServiceGrpc.BacklinksServiceBlockingStub backlinksStub(
            @Value("${backlinks.grpc.host}") String host,
            @Value("${backlinks.grpc.port}") int port) {
        var channel = ManagedChannelBuilder.forAddress(host, port)
            .usePlaintext()
            .build();
        return BacklinksServiceGrpc.newBlockingStub(channel);
    }
}
```

Spring auto-wires the rest through component scanning: `BacklinksGrpcAdapter` (marked `@Component`) is the single implementation of `BacklinksPort`, so Spring injects it wherever `BacklinksPort` is required. No explicit bean definition needed for the adapter itself.

## Key Patterns

### Pattern: Dependency Inversion

Core depends on abstractions (ports), not concrete implementations (adapters).

```java
// Good - depends on port (abstraction)
@Service
class MessageService {
    private final DialoguePort dialogue;

    MessageService(DialoguePort dialogue) {
        this.dialogue = dialogue;
    }
}

// Bad - depends on concrete implementation
@Service
class MessageService {
    private final DialogueJdbcAdapter dialogue;  // Concrete!

    MessageService() {
        this.dialogue = new DialogueJdbcAdapter(new JdbcTemplate());
    }
}
```

### Pattern: Ports as Interfaces

Ports are Java interfaces with clear contracts. Not abstract classes.

```java
// Good - interface port
public interface DialoguePort {
    String ensureActive(long userId);
    Optional<String> findActive(long userId);
    int softDelete(long userId);
}

// Bad - abstract class port
public abstract class DialoguePort {
    public abstract String ensureActive(long userId);
    // Abstract classes carry baggage: constructors, state, inheritance coupling
}
```

### Pattern: Adapter Implements Port

Adapters implement port interfaces and provide concrete infrastructure logic.

```java
@Component
class DialogueJdbcAdapter implements DialoguePort {
    private final JdbcTemplate jdbc;

    DialogueJdbcAdapter(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public String ensureActive(long userId) {
        // Concrete JDBC implementation
        ...
    }
}
```

### Pattern: Spring @Configuration for Wiring

One configuration class where infrastructure beans are created. Component scanning handles the rest.

```java
@Configuration
class ApplicationConfig {

    @Bean
    BacklinksServiceBlockingStub backlinksStub(
            @Value("${backlinks.grpc.host}") String host,
            @Value("${backlinks.grpc.port}") int port) {
        var channel = ManagedChannelBuilder.forAddress(host, port)
            .usePlaintext()
            .build();
        return BacklinksServiceGrpc.newBlockingStub(channel);
    }

    // No need to manually wire BacklinksGrpcAdapter -> BacklinksPort.
    // Spring sees @Component on BacklinksGrpcAdapter and auto-injects it
    // wherever BacklinksPort is required (single implementation).
}
```

## Benefits

1. **Testability** -- Mock ports for unit tests, no real databases needed
2. **Flexibility** -- Swap adapters without changing domain logic
3. **Clarity** -- Clear boundaries between layers
4. **Independence** -- Domain logic has zero external dependencies

## Testing

Constructor injection makes testing straightforward. Mock the port interface, inject the mock.

```java
// Unit test - mock the port, test the service
@ExtendWith(MockitoExtension.class)
class BacklinksAnalysisServiceTest {

    @Mock
    private BacklinksPort backlinks;

    private BacklinksAnalysisService service;

    @BeforeEach
    void setUp() {
        service = new BacklinksAnalysisService(backlinks);
    }

    @Test
    void analyzeShouldReturnHighRiskForLowScore() {
        when(backlinks.fetchData("example.com", UrlScope.ROOT_DOMAIN))
            .thenReturn(new BacklinksData(10, 15.0, List.of()));

        var result = service.analyze("example.com");

        assertThat(result.risk()).isEqualTo(RiskLevel.HIGH);
        verify(backlinks).fetchData("example.com", UrlScope.ROOT_DOMAIN);
    }
}
```

```java
// Integration test - use @SpringBootTest with real or test adapters
@SpringBootTest
class BacklinksControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private BacklinksPort backlinks;  // Replace the real adapter with a mock

    @Test
    void postBacklinksShouldReturnAnalysis() throws Exception {
        when(backlinks.fetchData(any(), any()))
            .thenReturn(new BacklinksData(100, 75.0, List.of()));

        mockMvc.perform(post("/backlinks")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"url": "example.com"}
                    """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.risk").value("LOW"));
    }
}
```

```java
// Testing adapter in isolation
class BacklinksGrpcAdapterTest {

    @Test
    void fetchDataShouldTranslateProtobufToDomain() {
        var mockStub = mock(BacklinksServiceBlockingStub.class);
        var adapter = new BacklinksGrpcAdapter(mockStub);

        var protoResponse = BacklinksResponse.newBuilder()
            .setTotalBacklinks(42)
            .setAuthorityScore(88.5)
            .build();
        when(mockStub.summary(any())).thenReturn(protoResponse);

        var result = adapter.fetchData("example.com", UrlScope.ROOT_DOMAIN);

        assertThat(result.total()).isEqualTo(42);
        assertThat(result.score()).isEqualTo(88.5);
    }
}
```
