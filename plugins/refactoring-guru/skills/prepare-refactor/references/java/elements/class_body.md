# Class Body Rules

## Private Final Fields

All fields should be `private final`. This enforces immutability and makes dependencies explicit. No package-private, no protected, no mutable fields.

```java
// Bad - mutable, non-private fields
public class BacklinksService {
    UserRepository repository;
    protected Cache cache;
    private HttpClient client;

    public BacklinksService(UserRepository repository, Cache cache, HttpClient client) {
        this.repository = repository;
        this.cache = cache;
        this.client = client;
    }
}

// Good - private final fields
public class BacklinksService {
    private final UserRepository repository;
    private final Cache cache;
    private final HttpClient client;

    public BacklinksService(UserRepository repository, Cache cache, HttpClient client) {
        this.repository = repository;
        this.cache = cache;
        this.client = client;
    }
}
```

## Always Use `this` for Field Access

Every reference to a field must be qualified with `this.` — in constructors, methods, and lambdas. This makes it immediately clear whether a name refers to a field or a local variable.

```java
// Bad - bare field access
public class BacklinksService {
    private final BacklinksRepository repository;
    private final int maxResults;

    public BacklinksService(BacklinksRepository repository, int maxResults) {
        this.repository = repository;
        this.maxResults = maxResults;
    }

    public List<Backlink> fetchBacklinks(String url) {
        return repository.findByUrl(url, maxResults);
    }
}

// Good - this. everywhere
public class BacklinksService {
    private final BacklinksRepository repository;
    private final int maxResults;

    public BacklinksService(BacklinksRepository repository, int maxResults) {
        this.repository = repository;
        this.maxResults = maxResults;
    }

    public List<Backlink> fetchBacklinks(String url) {
        return this.repository.findByUrl(url, this.maxResults);
    }
}
```

## Constructor Dependency Injection

Receive dependencies through the constructor. No `@Autowired` on fields, no setter injection. The constructor is the single point where all dependencies are declared and assigned.

```java
// Bad - field injection (hides dependencies, untestable without reflection)
@Service
public class UserService {
    @Autowired
    private UserRepository repository;
    @Autowired
    private NotificationClient notificationClient;
}

// Bad - creates dependencies internally
@Service
public class UserService {
    private final UserRepository repository;
    private final NotificationClient notificationClient;

    public UserService() {
        this.repository = new JpaUserRepository();
        this.notificationClient = new HttpNotificationClient();
    }
}

// Good - constructor injection (explicit, testable, immutable)
@Service
public class UserService {
    private final UserRepository repository;
    private final NotificationClient notificationClient;

    public UserService(UserRepository repository, NotificationClient notificationClient) {
        this.repository = repository;
        this.notificationClient = notificationClient;
    }
}

// Usage in tests - pass mocks directly
var service = new UserService(mockRepository, mockNotificationClient);
```

## Use @RequiredArgsConstructor When All Fields Are Private Final

When every field is `private final`, use Lombok's `@RequiredArgsConstructor` instead of writing the constructor by hand. It generates the same constructor with no boilerplate.

Only `@RequiredArgsConstructor` and `@Slf4j` are permitted Lombok annotations. All others (`@Data`, `@Builder`, `@Getter`, `@Setter`, `@AllArgsConstructor`, `@NoArgsConstructor`, etc.) are banned — they generate hidden behaviour that breaks encapsulation or bypasses immutability rules.

```java
// Bad - manual constructor (boilerplate when all fields are final)
@Service
public class UserService {
    private final UserRepository repository;
    private final NotificationClient notificationClient;

    public UserService(UserRepository repository, NotificationClient notificationClient) {
        this.repository = repository;
        this.notificationClient = notificationClient;
    }
}

// Good - @RequiredArgsConstructor generates the same constructor
@RequiredArgsConstructor
@Service
public class UserService {
    private final UserRepository repository;
    private final NotificationClient notificationClient;
}
```

If you need telescoping constructors (defaults for optional parameters), write them manually — `@RequiredArgsConstructor` is not a substitute for multi-constructor design.

## Telescoping Constructors for Defaults

One primary constructor sets all fields. Convenience constructors delegate to it via `this(...)` with sensible defaults. Do NOT use static factory methods for default variations.

```java
// Bad - static factory methods for defaults
public class SpectrumAdapter {
    private final OverviewService overviewService;
    private final PositionService positionService;
    private final int timeout;

    public SpectrumAdapter(OverviewService overviewService, PositionService positionService, int timeout) {
        this.overviewService = overviewService;
        this.positionService = positionService;
        this.timeout = timeout;
    }

    public static SpectrumAdapter withDefaultTimeout(OverviewService overview, PositionService position) {
        return new SpectrumAdapter(overview, position, 30);
    }
}

// Good - telescoping constructors
public class SpectrumAdapter {
    private final OverviewService overviewService;
    private final PositionService positionService;
    private final int timeout;

    // Primary constructor
    public SpectrumAdapter(OverviewService overviewService, PositionService positionService, int timeout) {
        this.overviewService = overviewService;
        this.positionService = positionService;
        this.timeout = timeout;
    }

    // Convenience - default timeout
    public SpectrumAdapter(OverviewService overviewService, PositionService positionService) {
        this(overviewService, positionService, 30);
    }
}

// Usage
var adapter = new SpectrumAdapter(overviewService, positionService);      // default timeout
var adapter = new SpectrumAdapter(overviewService, positionService, 60);  // custom timeout
```

Key points:
- All convenience constructors delegate to the primary one via `this(...)`
- Defaults flow from most-defaulted to least-defaulted
- The primary constructor is the only place fields are assigned

## Immutable After Construction

Classes should be fully initialized in the constructor. No lazy initialization, no `null` placeholders that get filled later. After the constructor completes, the object is ready.

```java
// Bad - lazy initialization (mutable, null-prone)
public class BacklinksAdapter {
    private final Channel channel;
    private BacklinksStub stub;  // null until first use

    public BacklinksAdapter(Channel channel) {
        this.channel = channel;
    }

    private BacklinksStub getStub() {
        if (stub == null) {
            stub = new BacklinksStub(channel);
        }
        return stub;
    }
}

// Good - eager initialization (immutable, ready immediately)
public class BacklinksAdapter {
    private final Channel channel;
    private final BacklinksStub stub;

    public BacklinksAdapter(Channel channel) {
        this.channel = channel;
        this.stub = new BacklinksStub(channel);
    }
}

// Good - if stub creation is complex, inject it
public class BacklinksAdapter {
    private final BacklinksStub stub;

    public BacklinksAdapter(BacklinksStub stub) {
        this.stub = stub;
    }
}
```

## Method Organization

Order methods consistently: constructor, public API, then private helpers grouped by purpose.

```java
public class BacklinksService {
    private final BacklinksStub stub;
    private final int maxResults;

    // Constructor
    public BacklinksService(BacklinksStub stub, int maxResults) {
        this.stub = stub;
        this.maxResults = maxResults;
    }

    public BacklinksService(BacklinksStub stub) {
        this(stub, 100);
    }

    // Public API methods
    public BacklinksResponse getBacklinksList(String url) {
        var items = fetchBacklinks(url);
        return new BacklinksResponse(items);
    }

    public OverviewResponse getBacklinksOverview(String url) {
        // ...
    }

    // Private fetch methods
    private List<Backlink> fetchBacklinks(String url) {
        // ...
    }

    // Private conversion methods
    private Backlink convertBacklink(RawBacklink raw) {
        // ...
    }

    // Private utility methods
    private Request buildRequest(String url) {
        // ...
    }

    private int clampLimit(int limit) {
        // ...
    }
}
```

## Single Responsibility Per Class

Each class should have one clear purpose. Split large classes into focused collaborators.

```java
// Bad - multiple responsibilities
public class UserManager {
    public User createUser(CreateUserRequest req) { ... }
    public void sendWelcomeEmail(User user) { ... }
    public Report generateUserReport() { ... }
    public void backupUserData() { ... }
}

// Good - focused classes
public class UserService {
    public User createUser(CreateUserRequest req) { ... }
}

public class EmailService {
    public void sendWelcomeEmail(User user) { ... }
}

public class ReportGenerator {
    public Report generateUserReport() { ... }
}
```

## Records for Data Containers

Use records instead of verbose POJOs for classes that primarily hold data. Records provide `equals`, `hashCode`, `toString`, and accessors automatically. They are immutable by design.

```java
// Bad - verbose POJO
public class BacklinkItem {
    private final String url;
    private final int score;
    private final String anchor;

    public BacklinkItem(String url, int score, String anchor) {
        this.url = url;
        this.score = score;
        this.anchor = anchor;
    }

    public String url() { return url; }
    public int score() { return score; }
    public String anchor() { return anchor; }
    // plus equals, hashCode, toString...
}

// Good - record
public record BacklinkItem(String url, int score, String anchor) {}

// Records can have compact constructors for validation
public record Target(String url, UrlScope scope) {
    public Target {
        if (url == null || url.isBlank()) {
            throw new IllegalArgumentException("url must not be blank");
        }
    }
}
```

## Sealed Interfaces for Type Hierarchies

Use sealed interfaces with `permits` to define closed type hierarchies. This enables exhaustive pattern matching and prevents uncontrolled extension.

```java
// Bad - open hierarchy, anything can extend
public abstract class ExportResult {}
public class ExportSuccess extends ExportResult { ... }
public class ExportFailure extends ExportResult { ... }
// Anyone can add: public class ExportMaybe extends ExportResult { ... }

// Good - sealed hierarchy, compiler-checked exhaustiveness
public sealed interface ExportResult permits ExportResult.Success, ExportResult.Failure {
    record Success(String fileUrl, long sizeBytes) implements ExportResult {}
    record Failure(String reason, int errorCode) implements ExportResult {}
}

// Exhaustive switch (compiler warns if a case is missing)
return switch (result) {
    case ExportResult.Success s -> downloadFile(s.fileUrl());
    case ExportResult.Failure f -> handleError(f.reason());
};
```

## Interfaces for Contracts

Use focused interfaces to define contracts. Each interface should represent a single capability. Classes implement the interfaces they need.

```java
// Bad - one fat interface
public interface DataService {
    User findUser(int id);
    void saveUser(User user);
    List<Backlink> getBacklinks(String url);
    Report generateReport(ReportConfig config);
    void sendNotification(String message);
}

// Good - focused interfaces
public interface UserRepository {
    Optional<User> findById(int id);
    void save(User user);
}

public interface BacklinksClient {
    List<Backlink> getBacklinks(String url);
}

public interface NotificationSender {
    void send(String message);
}

// Classes implement only what they need
public class PostgresUserRepository implements UserRepository {
    private final JdbcTemplate jdbc;

    public PostgresUserRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public Optional<User> findById(int id) { ... }

    @Override
    public void save(User user) { ... }
}
```
