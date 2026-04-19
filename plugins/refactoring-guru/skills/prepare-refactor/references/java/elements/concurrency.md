# Concurrency Patterns

## Stream Pipelines Over Manual Loops

Use stream pipelines (`filter().map().limit()...`) instead of manual for loops. Pipelines declare intent and compose naturally. Prefer **StreamEx** over standard streams for richer operations (`sortedBy`, `groupingBy`, `zipWith`, etc.).

```java
// Bad - manual loop
List<Item> items = new ArrayList<>();
for (var raw : rawItems) {
    items.add(convert(raw));
}

// Good - stream pipeline
var items = StreamEx.of(rawItems)
    .map(this::convert)
    .toList();
```

## Pipeline Filtering and Sorting

Chain `filter` before `map` to skip unwanted elements early. Use `sortedBy` for readable sorting.

```java
// Bad - manual loop with condition and sorting
List<Item> items = new ArrayList<>();
for (var raw : rawItems) {
    if (raw.active()) {
        items.add(convert(raw));
    }
}
items.sort(Comparator.comparingInt(Item::score).reversed());

// Good - pipeline with filter, map, sort
var items = StreamEx.of(rawItems)
    .filter(RawItem::active)
    .map(this::convert)
    .reverseSorted(Comparator.comparingInt(Item::score))
    .toList();
```

## Parallel Execution with CompletableFuture

Use `CompletableFuture.allOf` for independent async operations that can run concurrently.

```java
// Bad - sequential execution
var users = fetchUsers();
var orders = fetchOrders();
var products = fetchProducts();

// Good - parallel execution
var usersFuture = CompletableFuture.supplyAsync(this::fetchUsers);
var ordersFuture = CompletableFuture.supplyAsync(this::fetchOrders);
var productsFuture = CompletableFuture.supplyAsync(this::fetchProducts);

CompletableFuture.allOf(usersFuture, ordersFuture, productsFuture).join();

var users = usersFuture.join();
var orders = ordersFuture.join();
var products = productsFuture.join();
```

## Parallel Execution with Error Handling

Use `handle` or `exceptionally` when you want to collect partial failures instead of failing fast.

```java
// Bad - one failure cancels all
var users = CompletableFuture.supplyAsync(this::fetchUsers).join();
var orders = CompletableFuture.supplyAsync(this::fetchOrders).join();

// Good - collect results and errors
var usersFuture = CompletableFuture.supplyAsync(this::fetchUsers)
    .exceptionally(ex -> {
        logger.warn("event=fetch_users_failed error={}", ex.getMessage());
        return List.of();
    });
var ordersFuture = CompletableFuture.supplyAsync(this::fetchOrders)
    .exceptionally(ex -> {
        logger.warn("event=fetch_orders_failed error={}", ex.getMessage());
        return List.of();
    });

CompletableFuture.allOf(usersFuture, ordersFuture).join();
var users = usersFuture.join();
var orders = ordersFuture.join();
```

## Virtual Threads for I/O

Use virtual threads (Project Loom, Java 21+) for I/O-bound work. They scale to millions of concurrent tasks without platform thread exhaustion.

```java
// Bad - platform thread pool for I/O
var executor = Executors.newFixedThreadPool(10);
var futures = urls.stream()
    .map(url -> executor.submit(() -> fetch(url)))
    .toList();

// Good - virtual threads for I/O
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    var futures = urls.stream()
        .map(url -> executor.submit(() -> fetch(url)))
        .toList();

    var results = futures.stream()
        .map(f -> {
            try { return f.get(); }
            catch (Exception e) { throw new RuntimeException(e); }
        })
        .toList();
}
```

## Timeout for External Calls

Always set timeouts for external calls to prevent hanging. Use `orTimeout` on `CompletableFuture` or configure timeouts on HTTP/gRPC clients directly.

```java
// Bad - no timeout
var result = CompletableFuture.supplyAsync(() -> externalApi.fetchUser(userId)).join();

// Good - explicit timeout on future
var result = CompletableFuture.supplyAsync(() -> externalApi.fetchUser(userId))
    .orTimeout(30, TimeUnit.SECONDS)
    .exceptionally(ex -> {
        logger.warn("event=fetch_user_timeout user_id={}", userId);
        return defaultUser;
    })
    .join();

// Good - timeout configured on the client
var client = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(5))
    .build();

var request = HttpRequest.newBuilder()
    .uri(URI.create(url))
    .timeout(Duration.ofSeconds(30))
    .build();
```

## Try-with-Resources for Resource Cleanup

Use try-with-resources for anything that implements `AutoCloseable`. This guarantees cleanup even when exceptions occur.

```java
// Bad - manual cleanup
var client = createClient();
try {
    return client.fetch();
} finally {
    client.close();
}

// Good - try-with-resources
try (var client = createClient()) {
    return client.fetch();
}

// Good - multiple resources
try (var conn = dataSource.getConnection();
     var stmt = conn.prepareStatement(sql);
     var rs = stmt.executeQuery()) {
    return mapResults(rs);
}
```

## Semaphore for Rate Limiting

Use `Semaphore` to limit concurrent operations against external services.

```java
// Bad - unbounded concurrency
public List<Response> fetchAll(List<String> urls) {
    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
        return urls.stream()
            .map(url -> executor.submit(() -> fetch(url)))
            .map(f -> {
                try { return f.get(); }
                catch (Exception e) { throw new RuntimeException(e); }
            })
            .toList();
    }
}

// Good - bounded concurrency with semaphore
public List<Response> fetchAll(List<String> urls, int maxConcurrent) {
    var semaphore = new Semaphore(maxConcurrent);

    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
        return urls.stream()
            .map(url -> executor.submit(() -> {
                semaphore.acquire();
                try {
                    return fetch(url);
                } finally {
                    semaphore.release();
                }
            }))
            .map(f -> {
                try { return f.get(); }
                catch (Exception e) { throw new RuntimeException(e); }
            })
            .toList();
    }
}
```
