# Naming Rules

## Names Read Naturally at the Call Site

The ultimate test for any name — field, variable, method, or parameter — is how it reads where it's used. If the call site reads like natural language, the names are good.

```java
// Good - reads naturally at the call site
var token = jwt.from(user);               // "jwt from user"
var backlinks = repository.findBy(url);   // "repository find by url"
var report = exporter.toPdf(data);        // "exporter to pdf data"
if (cache.has(key)) { ... }              // "cache has key"

// Bad - reads awkwardly or redundantly
var token = jwtProvider.generateTokenFromUserId(userId);
var backlinks = backlinkRepository.findBacklinksByUrl(targetUrl);
var report = reportExporter.exportReportToPdf(reportData);
if (cacheService.checkCacheContainsKey(cacheKey)) { ... }
```

A natural reading is built from these parts: **result** = **receiver** . **method** ( **argument** ).

```
var token = jwt.from(user);
    ─────   ───  ────  ────
    result  receiver method argument
```

Each part contributes context — so no single part needs to carry all the meaning. That's why `jwt.from(user)` works but `jwtProvider.generateTokenFromUserId(userId)` doesn't: every part repeats what the others already say.

**This rule applies everywhere:** fields, local variables, method names, and parameters. When choosing a name, imagine the line of code that will use it and ask — does it read naturally?

## Context Gives Meaning to Generic Names

The method context provides meaning to local variables. Generic names like `request`, `items`, `result` are clear when the surrounding method name establishes context.

```java
// Good - method context makes generic names clear
public List<BacklinkItem> fetchBacklinks(String url) {
    var request = buildRequest(url);          // Clearly a backlinks request
    var items = new ArrayList<BacklinkItem>(); // Clearly backlink items
    stub.listBacklinks(request)
        .forEachRemaining(item -> items.add(convert(item)));
    return items;
}

public List<User> fetchUsers(int orgId) {
    var request = buildRequest(orgId);   // Clearly a users request
    var items = new ArrayList<User>();   // Clearly user items
    stub.listUsers(request)
        .forEachRemaining(item -> items.add(convert(item)));
    return items;
}
```

The same `request` and `items` names work in both methods because the method name (`fetchBacklinks` vs `fetchUsers`) provides the context.

## When Generic Names Fail

Generic names become unclear when the method itself is generic or does multiple things.

```java
// Bad - method name doesn't establish context
public Object process(Object data) {
    var result = transform(data);
    var temp = validate(result);
    return temp;
}

// Good - specific method name + generic locals work
public ProcessedOrder processOrder(Order order) {
    var validated = validate(order);        // Clear: validating the order
    var enriched = enrich(validated);       // Clear: enriching the validated order
    return new ProcessedOrder(enriched);
}

// Also good - when method is truly generic, qualify the names
public ProcessedEntity processEntity(Entity entity, EntityType type) {
    return switch (type) {
        case ORDER -> {
            var orderData = extractOrderData(entity);
            yield processOrderData(orderData);
        }
        case USER -> {
            var userData = extractUserData(entity);
            yield processUserData(userData);
        }
    };
}
```

## Drop Type Suffixes When Context Is Clear

When the method or class makes it obvious what an identifier represents, drop suffixes like `Id`, `Name`, `Count`. Keep the suffix only when ambiguity would arise.

```java
// Bad - suffix is redundant, method name already says "user"
public User findUser(long userId) { ... }
public void assignWorkflow(long workflowId, long userId) { ... }

// Good - context makes it clear these are identifiers
public User find(long user) { ... }
public void assign(long workflow, long user) { ... }

// Good - suffix needed when multiple IDs could be confused
public void transfer(long sourceId, long targetId) { ... }
public void link(long userId, long workflowId) { ... }
```

**Rule:** If removing the suffix leaves the meaning unambiguous, remove it. If it creates confusion (multiple IDs, mixed types), keep it.

## Boolean Variables and Methods

Boolean names should read naturally. Adjectives work as-is for variables. For methods, use prefixes that form questions.

```java
// Good - adjectives work without prefix for variables
boolean active = true;
boolean visible = false;
boolean enabled = true;

// Good - verb prefixes form natural questions for methods
public boolean hasPermission(User user) { ... }     // "has permission?" - natural
public boolean shouldRetry(int attempt) { ... }      // "should retry?" - natural
public boolean canEdit(User user, Document doc) { ... } // "can edit?" - natural

// Bad - unclear boolean intent
public boolean checkPermission(User user) { ... }    // Returns bool? Throws? Unclear
public boolean permission(User user) { ... }          // Not obviously boolean
```

**Rule:** If the name reads as a yes/no question without a prefix, skip the prefix. Use `has`/`should`/`can` prefixes on methods to signal boolean return.

## Collection Plurals

Use plural names for collections. Use singular for individual items.

```java
// Bad
var userList = fetchUsers();
for (var u : userList) { ... }

// Good
var users = fetchUsers();
for (var user : users) {
    process(user);
}
```

## Constants in SCREAMING_SNAKE_CASE

Class-level constants use uppercase with underscores.

```java
// Good
public class ApiConfig {
    private static final int DEFAULT_LIMIT = 10;
    private static final int MAX_RETRIES = 3;
    private static final Duration API_TIMEOUT = Duration.ofSeconds(30);
}
```

## Accessor Methods Without get Prefix

Use `name()` instead of `getName()`. Records follow this convention by default.

```java
// Bad - verbose getters
public String getName() { return name; }
public int getAge() { return age; }

// Good - clean accessors
public String name() { return name; }
public int age() { return age; }

// Records do this by default
public record User(String name, int age, boolean active) {}
// user.name(), user.age(), user.active() - no get prefix
```

Exception: When implementing interfaces that require `get` prefix (e.g., JavaBeans-based frameworks).

## No Single-Letter Names

Never use single-letter names, even in lambdas and loops. Use at least 3 letters — abbreviate if needed, but keep it readable.

```java
// Bad - single letter names
users.stream()
    .filter(u -> u.active())
    .toList();

for (var e : entries) {
    process(e);
}

contexts.forEach(c -> doSmth(c));

// Good - short but readable
users.stream()
    .filter(usr -> usr.active())
    .toList();

for (var entry : entries) {
    process(entry);
}

contexts.forEach(ctx -> doSmth(ctx));
```

## Name Length Matches Scope

These rules apply to **fields, local variables, and method names** equally.

Short scopes get short names. Wide scopes get descriptive names. A name should be just long enough to be clear in its context — no longer.

```java
// Good - short name in a tight scope
users.stream()
    .filter(usr -> usr.active())
    .toList();

// Good - one of its kind, drop the type suffix
private final BacklinksRepository repository;
private final NotificationService notifications;

// Good - multiple of the same kind, use a short qualifier
private final BacklinksRepository backlinkRepo;
private final UserRepository userRepo;
```

**Avoid compound names that repeat context already given by the type, class, or method.** The enclosing class name is part of every name's context — don't restate it.

```java
// Bad - name restates what the type already says
private final UserRepository userRepository;
public UserPermission getUserPermission(User user) { ... }
public BacklinkValidationResult validateBacklinkData(BacklinkData data) { ... }

// Good - shorter, context comes from the class and types
private final UserRepository repository;
public Permission permission(User user) { ... }
public ValidationResult validate(BacklinkData data) { ... }
```

```java
// Bad - "Job" repeated in every name inside a job-related class
public class JobProcessor {
    private final List<Job> pendingJobs;
    private final List<Job> runningJobs;
    private final List<Job> staleJobs;

    public List<Job> findPendingJobs() { ... }
    public void markJobRunning(Job job) { ... }
}

// Good - class name already says "Job", drop the suffix
public class JobProcessor {
    private final List<Job> pending;
    private final List<Job> running;
    private final List<Job> stale;

    public List<Job> findPending() { ... }
    public void markRunning(Job job) { ... }
}
```

**Avoid names longer than 3 words** — for variables, fields, and methods alike. If a name needs 4+ words, the concept is likely too compound — extract a type or rethink the abstraction.

```java
// Bad - too many words crammed into one name
int maxAllowedRetryAttemptCount = 3;
UserAccountPermissionValidationResult result = validate(user);
public List<Backlink> fetchFilteredBacklinksByDomain(String domain) { ... }

// Good - simpler names, extract types if needed
int maxRetries = 3;
ValidationResult result = validate(user);
public List<Backlink> fetchBacklinks(String domain) { ... }
```

## Avoid Abbreviations

Use full words except for universally known abbreviations (URL, HTTP, ID, API).

```java
// Bad
public UserInfo usrInfo(int usrId) { ... }
public BigDecimal calcTtlAmt() { ... }

// Good
public UserInfo userInfo(int userId) { ... }
public BigDecimal calculateTotalAmount() { ... }

// OK - universal abbreviations
public String fetchUrl(String url) { ... }
public String apiKey() { ... }
```

## Method Naming by Action

Method names should indicate their action clearly.

**Simple accessors:** Use the field name directly, no prefix needed.

```java
// Bad - redundant prefix
public User getUser() { return user; }
public Config getConfig() { return config; }

// Good - name is what it returns
public User user() { return user; }
public Config config() { return config; }
```

**Action methods:** Use prefixes that describe the action.

| Prefix | Meaning | Example |
|---|---|---|
| `fetch` | Retrieve from external source | `fetchUser()` |
| `create` | Create and return new instance | `createOrder()` |
| `build` | Construct from parts | `buildRequest()` |
| `parse` | Extract structure from raw | `parseResponse()` |
| `validate` | Check and return valid/throw | `validateInput()` |
| `convert` | Transform between types | `convertToDto()` |
| `handle` | Process/react to something | `handleError()` |
