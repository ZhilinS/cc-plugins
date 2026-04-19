# Method Signature Rules

## Type Safety Over Magic Strings

Use enums for constrained parameters. This enables IDE autocomplete, exhaustive switch checks, and catches invalid values at compile time.

```java
// Bad - any string accepted
public List<Backlink> fetch(String sortDirection) { ... }
fetch("descending"); // compiles, but wrong at runtime

// Good - constrained to valid values
public enum SortDirection { ASC, DESC }

public List<Backlink> fetch(SortDirection sortDirection) { ... }
fetch(SortDirection.DESC); // compiler-checked
```

## Named Parameters via Record

When a method takes 3+ parameters, group them into a request record. This eliminates argument-order mistakes and makes call sites self-documenting.

```java
// Bad - positional parameter soup
public BacklinksResponse backlinks(String url, String scope, int limit, SortDirection direction) { ... }
backlinks("example.com", "page", 10, SortDirection.DESC); // which string is which?

// Good - request record groups related params
public record BacklinksRequest(String url, String scope, int limit, SortDirection direction) {
    public BacklinksRequest(String url, String scope) {
        this(url, scope, 100, SortDirection.DESC);
    }
}

public BacklinksResponse backlinks(BacklinksRequest request) { ... }

// Call site is clear
backlinks(new BacklinksRequest("example.com", "page", 10, SortDirection.DESC));
backlinks(new BacklinksRequest("example.com", "page")); // with defaults
```

## Default Values via Overloads

Provide sensible defaults through telescoping constructors and method overloads. Put required parameters first.

```java
// Bad - callers must specify everything
public List<User> search(String query, int limit, int offset, boolean includeInactive) { ... }
search("john", 50, 0, false); // forced to know all defaults

// Good - overloads provide defaults
public List<User> search(String query, int limit, int offset) {
    return searchUsers(query, limit, offset);
}

public List<User> search(String query, int limit) {
    return search(query, limit, 0);
}

public List<User> search(String query) {
    return search(query, 50);
}

// Callers pick the level of control they need
search("john");
search("john", 20);
search("john", 20, 100);
```

## Return Optional Instead of Null

Never return null. Use `Optional` for methods that may not produce a result. This forces callers to handle absence explicitly.

```java
// Bad - null return, caller might forget to check
public User findUser(long userId) {
    return db.find(userId); // null if not found
}
var name = findUser(42).name(); // NullPointerException

// Good - Optional makes absence explicit
public Optional<User> findUser(long userId) {
    return db.findById(userId);
}
var name = findUser(42)
    .map(User::name)
    .orElse("unknown");
```

For collections, return empty collections instead of null:

```java
// Bad
public List<Order> orders(long userId) {
    var result = db.query(userId);
    return result; // caller must null-check
}

// Good
public List<Order> orders(long userId) {
    return db.query(userId); // returns empty list when no results
}
```

## Method Naming Patterns

Follow consistent naming patterns:

| Pattern | Purpose | Example |
|---------|---------|---------|
| `*` (noun) | Public API, returns data | `backlinks()` or `backlinksList()` |
| `fetch*` | Data fetching (remote/IO) | `fetchBacklinks()` |
| `convert*` | Transform between types | `convertBacklink()` |
| `build*` | Construct objects | `buildRequest()` |
| `validate*` | Input validation | `validateLimit()` |
| `handle*` | Process events or results | `handleError()` |

```java
// Good - clear naming hierarchy
public class BacklinksService {
    private final BacklinksClient client;

    // Public API - orchestrates the flow
    public BacklinksResponse backlinks(String url) {
        var items = fetchBacklinks(url);
        return new BacklinksResponse(items);
    }

    // Fetching - handles data retrieval
    private List<BacklinkItem> fetchBacklinks(String url) {
        var request = buildRequest(url);
        var raw = client.query(request);
        return raw.stream()
            .map(this::convertBacklink)
            .toList();
    }

    // Construction - builds request objects
    private BacklinksRequest buildRequest(String url) { ... }

    // Transformation - converts between types
    private BacklinkItem convertBacklink(RawBacklink raw) { ... }
}
```

## Avoid Boolean Parameters

Boolean parameters obscure meaning at call sites. Use enums or separate methods.

```java
// Bad - what does true mean here?
public List<User> users(boolean includeDeleted) { ... }
users(true); // true what?

// Good - enum makes intent explicit
public enum UserFilter { ACTIVE, ALL }

public List<User> users(UserFilter filter) { ... }
users(UserFilter.ALL); // clear intent

// Also good - separate methods when the logic diverges significantly
public List<User> activeUsers() { ... }
public List<User> allUsers() { ... }
```

## Prefer Specific Types Over Primitives

Wrap primitive values in domain types. This prevents mixing up parameters of the same raw type and makes signatures self-documenting.

```java
// Bad - primitives are interchangeable, easy to swap by accident
public Order findOrder(long userId, long orderId) { ... }
findOrder(orderId, userId); // compiles, wrong at runtime

// Good - domain types prevent mix-ups
public record UserId(long value) {}
public record OrderId(long value) {}

public Order findOrder(UserId userId, OrderId orderId) { ... }
findOrder(orderId, userId); // compile error

// Good - also useful for string identifiers
public record Email(String value) {}
public record Slug(String value) {}

public User findByEmail(Email email) { ... }
findByEmail(new Email("john@example.com"));
```
