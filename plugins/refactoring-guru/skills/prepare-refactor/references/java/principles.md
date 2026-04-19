# Java Style Principles

## Prefer Final Fields Everywhere

All fields should be `final`. If a field doesn't change after construction, declare it `final`. This makes classes immutable by default and easier to reason about.

```java
// Bad - mutable fields
public class UserService {
    private UserRepository repository;
    private Cache cache;

    public UserService(UserRepository repository, Cache cache) {
        this.repository = repository;
        this.cache = cache;
    }
}

// Good - final fields
public class UserService {
    private final UserRepository repository;
    private final Cache cache;

    public UserService(UserRepository repository, Cache cache) {
        this.repository = repository;
        this.cache = cache;
    }
}
```

Why:
- **Thread safety** — Final fields are safely published across threads
- **Intent** — Clearly communicates "this won't change"
- **Compiler help** — Catches accidental reassignment

## Prefer No Setters

Classes should be fully initialized via constructor. No setters, no mutability after construction.

```java
// Bad - mutable via setters
public class Config {
    private String host;
    private int port;

    public void setHost(String host) { this.host = host; }
    public void setPort(int port) { this.port = port; }
}

// Good - immutable, set via constructor
public class Config {
    private final String host;
    private final int port;

    public Config(String host, int port) {
        this.host = host;
        this.port = port;
    }

    public String host() { return host; }
    public int port() { return port; }
}

// Good - record for pure data
public record Config(String host, int port) {}
```

## Prefer Accessor Methods Without get Prefix

Use `name()` instead of `getName()`. The `get` prefix adds noise without value.

```java
// Bad - verbose getters
public String getName() { return name; }
public int getAge() { return age; }
public boolean isActive() { return active; }

// Good - clean accessors
public String name() { return name; }
public int age() { return age; }
public boolean active() { return active; }
```

Records follow this convention by default:
```java
public record User(String name, int age, boolean active) {}
// user.name(), user.age(), user.active() — no get prefix
```

Exception: When implementing interfaces that require `get` prefix (e.g., JavaBeans-based frameworks).

## Prefer Constructor Injection

Dependencies should be injected through the constructor, not via field injection or setters.

```java
// Bad - field injection (hides dependencies, untestable without reflection)
@Service
public class OrderService {
    @Autowired
    private PaymentClient paymentClient;
    @Autowired
    private InventoryClient inventoryClient;
}

// Good - constructor injection (explicit, testable)
@Service
public class OrderService {
    private final PaymentClient paymentClient;
    private final InventoryClient inventoryClient;

    public OrderService(PaymentClient paymentClient, InventoryClient inventoryClient) {
        this.paymentClient = paymentClient;
        this.inventoryClient = inventoryClient;
    }
}
```

Why:
- **Testable** — Pass mocks directly in tests
- **Explicit** — Dependencies visible in constructor
- **Immutable** — Fields can be `final`

## Prefer Composition Over Inheritance

Build behavior by composing objects rather than deep inheritance hierarchies. Use interfaces for contracts.

```java
// Bad - inheritance hierarchy
public abstract class BaseService {
    protected void log(String msg) { ... }
    protected void validate(Object obj) { ... }
}

public class UserService extends BaseService {
    public User findUser(int id) { ... }
}

public class AdminService extends UserService {
    public void deleteUser(int id) { ... }
}

// Good - composition
public class UserService {
    private final Logger logger;
    private final Validator validator;
    private final UserRepository repository;

    public UserService(Logger logger, Validator validator, UserRepository repository) {
        this.logger = logger;
        this.validator = validator;
        this.repository = repository;
    }
}
```

## Prefer Sealed Interfaces Over Class Hierarchies

Use sealed interfaces to define closed type hierarchies. This enables exhaustive pattern matching and prevents uncontrolled extension.

```java
// Bad - open hierarchy, anything can extend
public abstract class ApiResponse { }
public class SuccessResponse extends ApiResponse { ... }
public class ErrorResponse extends ApiResponse { ... }

// Good - sealed hierarchy, compiler-checked exhaustiveness
public sealed interface ApiResponse permits Success, Error {
    record Success(List<Item> items) implements ApiResponse {}
    record Error(String message, int code) implements ApiResponse {}
}

// Exhaustive switch (compiler warns if case is missing)
return switch (response) {
    case ApiResponse.Success s -> renderItems(s.items());
    case ApiResponse.Error e -> renderError(e.message());
};
```

## Prefer Records for Data Containers

Use records for classes that primarily hold data. They provide `equals`, `hashCode`, `toString`, and accessors for free.

```java
// Bad - verbose boilerplate
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
```

## Prefer Data Pipelines Over Method Chains

Use stream-style pipelines (`filter().map().limit()...`) for data transformations. Libraries like **StreamEx** extend the standard Stream API with richer operations. This is about chaining data transformations — NOT about builder patterns that return object instances.

```java
// Bad - imperative loop with accumulation
public List<BacklinkItem> topActiveBacklinks(List<RawBacklink> raw, int limit) {
    var result = new ArrayList<BacklinkItem>();
    for (var item : raw) {
        if (item.active() && item.score() > 50) {
            result.add(convert(item));
            if (result.size() >= limit) {
                break;
            }
        }
    }
    result.sort(Comparator.comparingInt(BacklinkItem::score).reversed());
    return result;
}

// Good - pipeline declares intent
public List<BacklinkItem> topActiveBacklinks(List<RawBacklink> raw, int limit) {
    return StreamEx.of(raw)
        .filter(RawBacklink::active)
        .filter(item -> item.score() > 50)
        .map(this::convert)
        .sortedBy(BacklinkItem::score, Comparator.reverseOrder())
        .limit(limit)
        .toList();
}
```

```java
// Bad - builder pattern returning instances (not a data pipeline)
var result = new BacklinksQuery()
    .withUrl(url)
    .withLimit(10)
    .withSort(SortDirection.DESC)
    .execute();

// Good - pipeline transforms data, records hold parameters
var request = new BacklinksRequest(url, 10, SortDirection.DESC);
var result = service.backlinks(request);
```

Key distinction:
- **Pipeline** = transforming data through stages (`filter`, `map`, `limit`, `groupBy`) — preferred
- **Builder** = constructing an object by returning `this` from setters — use records instead

## Prefer Extract Helper Over Inline Logic

When a method grows beyond 15-20 lines, extract logical chunks into private helper methods. Name helpers by what they do.

```java
// Bad - long method with multiple responsibilities
public Result processOrder(Order order) {
    // 50 lines of validation, transformation, saving, notification...
}

// Good - orchestrator with focused helpers
public Result processOrder(Order order) {
    var validated = validateOrder(order);
    var transformed = transformForStorage(validated);
    var saved = saveOrder(transformed);
    notifyCompletion(saved);
    return new Result(saved.id());
}
```

## Prefer Explicit Over Implicit

Be explicit about types, return values, and behavior. Use `Optional` instead of returning null.

```java
// Bad - implicit null return
public User findUser(int userId) {
    return db.find(userId);  // Might return null
}

// Good - explicit Optional
public Optional<User> findUser(int userId) {
    return db.findById(userId);
}
```

## Prefer Telescoping Constructors for Defaults

One primary constructor sets all fields. Convenience constructors delegate to it with sensible defaults. This keeps the class immutable while providing flexible instantiation.

```java
// Bad - single constructor forces callers to specify everything
public class ApiClient {
    private final String host;
    private final Duration timeout;
    private final int maxRetries;

    public ApiClient(String host, Duration timeout, int maxRetries) {
        this.host = host;
        this.timeout = timeout;
        this.maxRetries = maxRetries;
    }
}
// Caller must know all defaults: new ApiClient("host", Duration.ofSeconds(30), 3)

// Good - primary constructor + convenience constructors with defaults
public class ApiClient {
    private final String host;
    private final Duration timeout;
    private final int maxRetries;

    // Primary constructor - sets all fields
    public ApiClient(String host, Duration timeout, int maxRetries) {
        this.host = host;
        this.timeout = timeout;
        this.maxRetries = maxRetries;
    }

    // Convenience - default retries
    public ApiClient(String host, Duration timeout) {
        this(host, timeout, 3);
    }

    // Convenience - default timeout and retries
    public ApiClient(String host) {
        this(host, Duration.ofSeconds(30));
    }
}

// Usage
var client = new ApiClient("https://api.example.com");                          // all defaults
var client = new ApiClient("https://api.example.com", Duration.ofSeconds(10));  // custom timeout
var client = new ApiClient("https://api.example.com", Duration.ofSeconds(10), 5); // full control
```

Key points:
- All convenience constructors delegate to the primary one via `this(...)`
- Defaults flow from most-defaulted to least-defaulted
- The primary constructor is the only place fields are assigned
