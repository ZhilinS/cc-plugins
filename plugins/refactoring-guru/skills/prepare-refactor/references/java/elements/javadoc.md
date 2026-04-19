# Javadoc Rules

**All Javadoc comments must be multiline.** No single-line `/** ... */` style, ever — even for short descriptions. This applies to classes, methods, fields, records, and interfaces.

```java
// Bad - single-line
/** jOOQ DSL context for building and executing SQL queries. */

// Good - always multiline
/**
 * jOOQ DSL context for building and executing SQL queries.
 */
```

## Class-Level Javadoc

Every class must have a Javadoc comment explaining what it does. Always multiline, even for short descriptions.

```java
// Bad - no Javadoc
public class BacklinksService {
    // ...
}

// Bad - single-line style
/** Fetches backlinks from the external API. */
public class BacklinksService {
    // ...
}

// Good - multiline Javadoc
/**
 * Fetches backlinks from the external API and converts
 * them into domain objects.
 */
public class BacklinksService {
    // ...
}

/**
 * Adapter for the Spectrum gRPC service that handles
 * overview and position data retrieval.
 */
public class SpectrumAdapter {
    // ...
}
```

Keep it concise - one to two sentences describing the class purpose. No `@author` or `@since` tags.

## Method-Level Javadoc

Every method (except `@Override`) must have a Javadoc comment, including constructors and private methods. Each Javadoc includes:
- A single-line description of what the method does
- `@param` for each parameter
- `@return` for the return value (skip for `void`)

```java
/**
 * Fetches backlinks for the given URL.
 *
 * @param url the target URL to fetch backlinks for
 * @param limit maximum number of results to return
 * @return list of backlinks sorted by authority score
 */
public List<Backlink> fetchBacklinks(String url, int limit) {
    // ...
}

/**
 * Sends a welcome email to a newly registered user.
 *
 * @param user the user to send the email to
 */
public void sendWelcomeEmail(User user) {
    // ...
}

/**
 * Checks whether the user has access to the given project.
 *
 * @param user the user to check permissions for
 * @param projectId the project identifier
 * @return true if the user has access, false otherwise
 */
public boolean hasAccess(User user, long projectId) {
    // ...
}
```

## Skip Javadoc on Overridden Methods

Methods annotated with `@Override` inherit documentation from the parent. Do not duplicate it.

```java
// Bad - redundant Javadoc on override
public class PostgresUserRepository implements UserRepository {

    /**
     * Finds a user by ID.
     *
     * @param id the user identifier
     * @return the user if found
     */
    @Override
    public Optional<User> findById(long id) {
        // ...
    }
}

// Good - no Javadoc on override
public class PostgresUserRepository implements UserRepository {

    @Override
    public Optional<User> findById(long id) {
        // ...
    }
}
```

## Field-Level Javadoc

Every field must have a Javadoc comment explaining its purpose.

```java
// Bad - no Javadoc
private final UserRepository userRepository;
private int retryCount;

// Bad - single-line style
/** Repository for user persistence operations. */
private final UserRepository userRepository;

// Good - always multiline
/**
 * Repository for user persistence operations.
 */
private final UserRepository userRepository;

/**
 * Number of retry attempts for failed requests.
 */
private int retryCount;
```

## Records and Interfaces

Records and interfaces follow the same class-level rule: multiline Javadoc on top.

```java
/**
 * Represents a single backlink with its source URL,
 * authority score, and anchor text.
 */
public record BacklinkItem(String url, int score, String anchor) {}

/**
 * Port for retrieving user data from the persistence layer.
 */
public interface UserRepository {

    /**
     * Finds a user by their unique identifier.
     *
     * @param id the user identifier
     * @return the user wrapped in Optional, empty if not found
     */
    Optional<User> findById(long id);

    /**
     * Persists the given user.
     *
     * @param user the user to save
     */
    void save(User user);
}
```

## Param Description Style

Start `@param` and `@return` descriptions in lowercase, no period at the end. Keep them on one line.

```java
// Bad - capitalized, period, verbose
/**
 * Fetches data.
 *
 * @param url The URL to fetch data from.
 * @param timeout The timeout in milliseconds for the request.
 * @return Returns a list of fetched items from the API.
 */

// Good - lowercase, no period, concise
/**
 * Fetches data from the external API.
 *
 * @param url the target URL to fetch data from
 * @param timeout timeout in milliseconds
 * @return list of fetched items
 */
```
