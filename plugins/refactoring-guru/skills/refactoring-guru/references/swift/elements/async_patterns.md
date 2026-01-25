# Async Patterns

## Structured Concurrency with TaskGroup

Use TaskGroup for parallel independent operations. Sequential awaits waste time when operations don't depend on each other.

```swift
// Bad - sequential awaits for independent operations
func loadDashboard() async throws -> Dashboard {
    let user = try await userService.fetchUser()
    let orders = try await orderService.fetchOrders()
    let recommendations = try await recommendationService.fetch()

    return Dashboard(user: user, orders: orders, recommendations: recommendations)
}

// Good - parallel execution with async let
func loadDashboard() async throws -> Dashboard {
    async let user = userService.fetchUser()
    async let orders = orderService.fetchOrders()
    async let recommendations = recommendationService.fetch()

    return try await Dashboard(user: user, orders: orders, recommendations: recommendations)
}

// Good - TaskGroup for dynamic number of parallel operations
func loadAllUserProfiles(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask {
                try await self.userService.fetchUser(id: id)
            }
        }

        var users: [User] = []
        for try await user in group {
            users.append(user)
        }
        return users
    }
}
```

## Actor for Shared Mutable State

Use actors when multiple tasks access shared mutable state. Classes with shared state create data races.

```swift
// Bad - class with data race potential
class Cache {
    private var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        storage[key]
    }

    func set(_ key: String, data: Data) {
        storage[key] = data  // Data race when called from multiple tasks
    }
}

// Good - actor ensures safe concurrent access
actor Cache {
    private var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        storage[key]
    }

    func set(_ key: String, data: Data) {
        storage[key] = data  // Safe - actor serializes access
    }
}

// Usage
let cache = Cache()
await cache.set("user", data: userData)
let data = await cache.get("user")
```

## MainActor for UI Updates

Annotate ViewModels and UI-updating code with @MainActor. UI updates from background threads cause crashes and undefined behavior.

```swift
// Bad - UI updates not guaranteed on main thread
@Observable
class ProfileViewModel {
    var user: User?
    var isLoading = false

    func loadProfile() async {
        isLoading = true  // May not be on main thread

        do {
            user = try await userService.fetchProfile()  // UI update from background
        } catch {
            // handle error
        }

        isLoading = false  // May not be on main thread
    }
}

// Good - @MainActor ensures all UI state updates on main thread
@MainActor
@Observable
class ProfileViewModel {
    var user: User?
    var isLoading = false

    func loadProfile() async {
        isLoading = true  // Guaranteed main thread

        do {
            user = try await userService.fetchProfile()
        } catch {
            // handle error
        }

        isLoading = false  // Guaranteed main thread
    }
}

// Good - isolated main actor usage for specific updates
@Observable
class DataProcessor {
    func processAndUpdateUI(data: Data) async {
        let processed = await heavyProcessing(data)  // Background

        await MainActor.run {
            // Only UI updates on main thread
            NotificationCenter.default.post(name: .dataProcessed, object: processed)
        }
    }
}
```

## Cancellation Handling

Check for cancellation in long-running operations. Ignoring cancellation wastes resources and delays user-initiated changes.

```swift
// Bad - ignores cancellation, continues processing after task cancelled
func processLargeDataset(_ items: [Item]) async throws -> [ProcessedItem] {
    var results: [ProcessedItem] = []

    for item in items {
        let processed = try await process(item)  // Continues even if cancelled
        results.append(processed)
    }

    return results
}

// Good - checks cancellation and exits early
func processLargeDataset(_ items: [Item]) async throws -> [ProcessedItem] {
    var results: [ProcessedItem] = []

    for item in items {
        try Task.checkCancellation()  // Throws if cancelled

        let processed = try await process(item)
        results.append(processed)
    }

    return results
}

// Good - cancellation handler for cleanup
func downloadAndCache(url: URL) async throws -> Data {
    let tempFile = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)

    return try await withTaskCancellationHandler {
        let (data, _) = try await URLSession.shared.data(from: url)
        try data.write(to: tempFile)
        return data
    } onCancel: {
        // Cleanup on cancellation
        try? FileManager.default.removeItem(at: tempFile)
    }
}
```

## AsyncSequence for Streams

Use AsyncSequence for data that arrives over time. Callbacks and delegates create pyramid-of-doom code and scattered state.

```swift
// Bad - callback-based message observation
class MessageObserver {
    var onMessage: ((Message) -> Void)?
    var onError: ((Error) -> Void)?
    var onComplete: (() -> Void)?

    func startObserving() {
        socket.onReceive = { [weak self] data in
            guard let message = try? JSONDecoder().decode(Message.self, from: data) else {
                self?.onError?(DecodingError.dataCorrupted(...))
                return
            }
            self?.onMessage?(message)
        }
    }
}

// Usage creates nested callbacks
observer.onMessage = { message in
    processMessage(message) { result in
        updateUI(result) { ... }
    }
}

// Good - AsyncStream for clean sequential processing
func observeMessages() -> AsyncStream<Message> {
    AsyncStream { continuation in
        let task = socket.onReceive { data in
            if let message = try? JSONDecoder().decode(Message.self, from: data) {
                continuation.yield(message)
            }
        }

        continuation.onTermination = { _ in
            task.cancel()
        }
    }
}

// Usage is linear and readable
func handleMessages() async {
    for await message in observeMessages() {
        let result = await processMessage(message)
        await updateUI(with: result)
    }
}
```

## Timeout for Async Operations

Wrap external calls with timeout. Unbounded awaits can hang indefinitely, blocking user actions.

```swift
// Bad - unbounded await can hang forever
func fetchUserData() async throws -> UserData {
    try await externalAPI.fetchUser()  // No timeout - may never return
}

// Good - timeout with TaskGroup race pattern
func fetchUserData() async throws -> UserData {
    try await withThrowingTaskGroup(of: UserData.self) { group in
        group.addTask {
            try await self.externalAPI.fetchUser()
        }

        group.addTask {
            try await Task.sleep(for: .seconds(30))
            throw TimeoutError()
        }

        let result = try await group.next()!
        group.cancelAll()  // Cancel the loser
        return result
    }
}

// Good - reusable timeout wrapper
func withTimeout<T>(
    seconds: Double,
    operation: @escaping () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask {
            try await operation()
        }

        group.addTask {
            try await Task.sleep(for: .seconds(seconds))
            throw TimeoutError()
        }

        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}

// Usage
let userData = try await withTimeout(seconds: 30) {
    try await externalAPI.fetchUser()
}
```
