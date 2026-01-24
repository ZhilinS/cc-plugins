# Swift Refactoring Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Swift language support to the refactoring-guru plugin with iOS/macOS SwiftUI patterns.

**Architecture:** Mirror Python structure with Swift-specific adaptations. 11 files total: 1 principles, 7 elements, 3 architecture. Each file contains Bad/Good code examples following existing format.

**Tech Stack:** Swift 5.9+, SwiftUI, @Observable (iOS 17+), async/await, MVVM architecture

---

## Task 1: Create Swift Directory Structure

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/`
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/`
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/`

**Step 1: Create directories**

```bash
mkdir -p plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements
mkdir -p plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift
git commit -m "chore: add Swift directory structure for refactoring rules"
```

---

## Task 2: Create principles.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/principles.md`

**Step 1: Write principles.md**

```markdown
# Swift Style Principles

## Value Types First

Prefer structs over classes. Use classes only when you need identity, inheritance, or reference semantics.

```swift
// Bad - class for simple data
class UserData {
    var name: String
    var email: String

    init(name: String, email: String) {
        self.name = name
        self.email = email
    }
}

// Good - struct for data
struct User {
    let name: String
    let email: String
}
```

## Protocol-Oriented Design

Define behavior through protocols, not inheritance. Use protocol extensions for default implementations.

```swift
// Bad - inheritance hierarchy
class BaseService {
    func log(_ message: String) { ... }
    func validate() { ... }
}

class UserService: BaseService {
    func fetchUser() { ... }
}

// Good - protocol composition
protocol Logging {
    func log(_ message: String)
}

protocol Validating {
    func validate() -> Bool
}

extension Logging {
    func log(_ message: String) {
        print("[\(Date())] \(message)")
    }
}

struct UserService: Logging, Validating {
    func fetchUser() { ... }
    func validate() -> Bool { ... }
}
```

## Explicit Over Implicit

Avoid force unwrapping. Use `guard let` for early exits. Prefer explicit error handling.

```swift
// Bad - force unwrap and implicit behavior
func processUser(_ data: [String: Any]) -> User {
    let name = data["name"] as! String
    let age = data["age"] as! Int
    return User(name: name, age: age)
}

// Good - explicit unwrapping with early exit
func processUser(_ data: [String: Any]) -> User? {
    guard let name = data["name"] as? String,
          let age = data["age"] as? Int else {
        return nil
    }
    return User(name: name, age: age)
}
```

## Composition Over Inheritance

Build views from small, reusable components. Use ViewModifiers over base view classes.

```swift
// Bad - attempting inheritance with views
struct BaseCard: View {
    var body: some View {
        // Can't inherit from this
    }
}

// Good - composition with ViewModifier
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(.background)
            .cornerRadius(12)
            .shadow(radius: 4)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}

// Usage
Text("Hello").cardStyle()
```

## Immutability by Default

Use `let` unless mutation is required. Prefer immutable data models.

```swift
// Bad - mutable when not needed
var userName = "John"  // Never reassigned
var settings = Settings()  // Only read

// Good - immutable by default
let userName = "John"
let settings = Settings()

// Good - mutable only when needed
var counter = 0
counter += 1
```

## Fail Fast, Recover Gracefully

Validate inputs at boundaries. Use typed errors for recoverable failures. Crash on programmer errors.

```swift
// Bad - silent failure
func divide(_ a: Int, by b: Int) -> Int? {
    if b == 0 { return nil }
    return a / b
}

// Good - typed error for recoverable failure
enum MathError: Error {
    case divisionByZero
}

func divide(_ a: Int, by b: Int) throws -> Int {
    guard b != 0 else {
        throw MathError.divisionByZero
    }
    return a / b
}

// Good - precondition for programmer errors
func element(at index: Int, in array: [Int]) -> Int {
    precondition(index >= 0 && index < array.count, "Index out of bounds")
    return array[index]
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/principles.md
git commit -m "feat(swift): add principles.md with 6 core Swift principles"
```

---

## Task 3: Create elements/view_structure.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/view_structure.md`

**Step 1: Write view_structure.md**

```markdown
# View Structure

## Keep Views Under 50 Lines

Extract subviews when a view grows beyond 50 lines. The view name provides context for internal state.

```swift
// Bad - monolithic view
struct ProfileView: View {
    @State private var user: User?
    @State private var loading = false

    var body: some View {
        VStack {
            // 30 lines of header...
            // 40 lines of content...
            // 20 lines of footer...
        }
    }
}

// Good - composed from focused subviews
struct ProfileView: View {
    @State private var user: User?
    @State private var loading = false

    var body: some View {
        VStack {
            ProfileHeader(user: user)
            ProfileContent(user: user, loading: loading)
            ProfileFooter()
        }
    }
}
```

## Computed Properties for Conditional Content

Use computed properties to break complex conditional logic out of the body.

```swift
// Bad - complex conditionals in body
var body: some View {
    VStack {
        if loading {
            ProgressView()
        } else if let error = error {
            Text(error.localizedDescription)
                .foregroundStyle(.red)
        } else if let user = user {
            Text(user.name)
        } else {
            Text("No user")
        }
    }
}

// Good - computed property for content
var body: some View {
    VStack {
        content
    }
}

@ViewBuilder
private var content: some View {
    if loading {
        ProgressView()
    } else if let error {
        errorView(error)
    } else if let user {
        userView(user)
    } else {
        emptyView
    }
}
```

## ViewBuilder for Reusable Layouts

Use @ViewBuilder functions for layouts that accept content.

```swift
// Bad - duplicated layout code
struct CardA: View {
    var body: some View {
        VStack {
            Text("Title A")
        }
        .padding()
        .background(.background)
        .cornerRadius(12)
    }
}

struct CardB: View {
    var body: some View {
        VStack {
            Image(systemName: "star")
        }
        .padding()
        .background(.background)
        .cornerRadius(12)
    }
}

// Good - reusable card layout
struct Card<Content: View>: View {
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack {
            content()
        }
        .padding()
        .background(.background)
        .cornerRadius(12)
    }
}

// Usage
Card { Text("Title A") }
Card { Image(systemName: "star") }
```

## Avoid Logic in View Body

Delegate business logic to ViewModel. Views only describe UI.

```swift
// Bad - logic in view
struct OrderView: View {
    let items: [Item]

    var body: some View {
        let subtotal = items.reduce(0) { $0 + $1.price }
        let tax = subtotal * 0.08
        let total = subtotal + tax

        VStack {
            Text("Total: \(total, format: .currency(code: "USD"))")
        }
    }
}

// Good - ViewModel handles logic
@Observable
final class OrderViewModel {
    private(set) var items: [Item] = []

    var total: Decimal {
        let subtotal = items.reduce(0) { $0 + $1.price }
        let tax = subtotal * 0.08
        return subtotal + tax
    }
}

struct OrderView: View {
    let viewModel: OrderViewModel

    var body: some View {
        Text("Total: \(viewModel.total, format: .currency(code: "USD"))")
    }
}
```

## Extract Repeated Subviews

When the same pattern appears multiple times, extract it.

```swift
// Bad - repeated pattern
var body: some View {
    VStack {
        HStack {
            Image(systemName: "person")
            Text("Name")
            Spacer()
            Text(user.name)
        }
        HStack {
            Image(systemName: "envelope")
            Text("Email")
            Spacer()
            Text(user.email)
        }
        HStack {
            Image(systemName: "phone")
            Text("Phone")
            Spacer()
            Text(user.phone)
        }
    }
}

// Good - extracted row component
var body: some View {
    VStack {
        InfoRow(icon: "person", label: "Name", value: user.name)
        InfoRow(icon: "envelope", label: "Email", value: user.email)
        InfoRow(icon: "phone", label: "Phone", value: user.phone)
    }
}

struct InfoRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack {
            Image(systemName: icon)
            Text(label)
            Spacer()
            Text(value)
        }
    }
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/view_structure.md
git commit -m "feat(swift): add view_structure.md with SwiftUI composition patterns"
```

---

## Task 4: Create elements/viewmodel_design.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/viewmodel_design.md`

**Step 1: Write viewmodel_design.md**

```markdown
# ViewModel Design

## One ViewModel Per Screen

Each screen/feature gets its own ViewModel. Avoid god-object ViewModels.

```swift
// Bad - shared ViewModel for multiple screens
@Observable
final class AppViewModel {
    var users: [User] = []
    var orders: [Order] = []
    var settings: Settings = .default
    var currentUser: User?
    // ... 50 more properties
}

// Good - focused ViewModel per screen
@Observable
final class UserListViewModel {
    private(set) var users: [User] = []
    private(set) var loading = false
}

@Observable
final class OrderHistoryViewModel {
    private(set) var orders: [Order] = []
    private(set) var loading = false
}
```

## Public Read-Only State

Use `private(set)` for state that views observe but shouldn't modify directly.

```swift
// Bad - fully mutable state
@Observable
final class ProfileViewModel {
    var user: User?
    var loading = false
    var error: Error?
}

// View can accidentally do: viewModel.loading = false

// Good - controlled mutations
@Observable
final class ProfileViewModel {
    private(set) var user: User?
    private(set) var loading = false
    private(set) var error: Error?

    func loadUser() async {
        loading = true
        defer { loading = false }

        do {
            user = try await userService.fetchCurrentUser()
        } catch {
            self.error = error
        }
    }
}
```

## Actions as Methods

Expose actions as methods, not published vars. Methods express intent.

```swift
// Bad - action as published var
@Observable
final class CounterViewModel {
    var count = 0
    var shouldIncrement = false  // View sets this to trigger action
}

// Good - action as method
@Observable
final class CounterViewModel {
    private(set) var count = 0

    func increment() {
        count += 1
    }

    func decrement() {
        count = max(0, count - 1)
    }
}
```

## Lifecycle with .task Modifier

Use SwiftUI's `.task` modifier for async initialization. It handles cancellation automatically.

```swift
// Bad - manual lifecycle management
struct UserView: View {
    let viewModel: UserViewModel

    var body: some View {
        content
            .onAppear {
                Task {
                    await viewModel.load()
                }
            }
            .onDisappear {
                viewModel.cancel()  // Manual cancellation
            }
    }
}

// Good - .task handles lifecycle
struct UserView: View {
    let viewModel: UserViewModel

    var body: some View {
        content
            .task {
                await viewModel.load()
            }
    }
}

// Task is automatically cancelled when view disappears
```

## State Enum for Complex States

Use an enum when a screen has multiple mutually exclusive states.

```swift
// Bad - multiple booleans
@Observable
final class DataViewModel {
    var loading = false
    var data: [Item]?
    var error: Error?
    var empty = false
    // Hard to ensure only one state is true
}

// Good - state enum
enum ViewState<T> {
    case idle
    case loading
    case loaded(T)
    case empty
    case error(Error)
}

@Observable
final class DataViewModel {
    private(set) var state: ViewState<[Item]> = .idle

    func load() async {
        state = .loading

        do {
            let items = try await service.fetch()
            state = items.isEmpty ? .empty : .loaded(items)
        } catch {
            state = .error(error)
        }
    }
}
```

## Dependency Injection via Initializer

Inject dependencies through the initializer for testability.

```swift
// Bad - creates own dependencies
@Observable
final class UserViewModel {
    private let service = UserService()

    func load() async { ... }
}

// Good - injected dependencies
@Observable
final class UserViewModel {
    private let service: UserServiceProtocol

    init(service: UserServiceProtocol = UserService()) {
        self.service = service
    }

    func load() async { ... }
}

// Test with mock
let mockService = MockUserService()
let viewModel = UserViewModel(service: mockService)
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/viewmodel_design.md
git commit -m "feat(swift): add viewmodel_design.md with @Observable patterns"
```

---

## Task 5: Create elements/async_patterns.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/async_patterns.md`

**Step 1: Write async_patterns.md**

```markdown
# Async Patterns

## Structured Concurrency with TaskGroup

Use TaskGroup for parallel independent operations.

```swift
// Bad - sequential execution
func fetchAllData() async throws -> (users: [User], orders: [Order]) {
    let users = try await fetchUsers()
    let orders = try await fetchOrders()
    return (users, orders)
}

// Good - parallel execution
func fetchAllData() async throws -> (users: [User], orders: [Order]) {
    async let users = fetchUsers()
    async let orders = fetchOrders()
    return try await (users, orders)
}

// Good - TaskGroup for dynamic number of tasks
func fetchAllUsers(ids: [Int]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask {
                try await fetchUser(id: id)
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

Use actors when multiple tasks access shared mutable state.

```swift
// Bad - shared state without synchronization
class Cache {
    var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        storage[key]  // Data race!
    }

    func set(_ key: String, value: Data) {
        storage[key] = value  // Data race!
    }
}

// Good - actor provides synchronization
actor Cache {
    private var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        storage[key]
    }

    func set(_ key: String, value: Data) {
        storage[key] = value
    }
}

// Usage
let cache = Cache()
await cache.set("user", value: userData)
let data = await cache.get("user")
```

## MainActor for UI Updates

Annotate ViewModels and UI-updating code with @MainActor.

```swift
// Bad - UI update from background
func loadData() async {
    let data = try? await service.fetch()
    self.items = data  // May crash if not on main thread
}

// Good - MainActor annotation
@MainActor
@Observable
final class DataViewModel {
    private(set) var items: [Item] = []

    func loadData() async {
        let data = try? await service.fetch()
        items = data ?? []  // Guaranteed main thread
    }
}

// Good - explicit MainActor hop for specific code
func process() async {
    let result = await heavyComputation()

    await MainActor.run {
        self.updateUI(with: result)
    }
}
```

## Cancellation Handling

Check for cancellation in long-running operations.

```swift
// Bad - ignores cancellation
func processItems(_ items: [Item]) async throws -> [Result] {
    var results: [Result] = []
    for item in items {
        let result = try await process(item)
        results.append(result)
    }
    return results
}

// Good - respects cancellation
func processItems(_ items: [Item]) async throws -> [Result] {
    var results: [Result] = []
    for item in items {
        try Task.checkCancellation()
        let result = try await process(item)
        results.append(result)
    }
    return results
}

// Good - cleanup on cancellation
func downloadFile(url: URL) async throws -> Data {
    let task = URLSession.shared.dataTask(with: url)

    return try await withTaskCancellationHandler {
        try await withCheckedThrowingContinuation { continuation in
            task.resume()
            // ... handle completion
        }
    } onCancel: {
        task.cancel()
    }
}
```

## AsyncSequence for Streams

Use AsyncSequence for data that arrives over time.

```swift
// Good - async sequence for streaming
func observeMessages() -> AsyncStream<Message> {
    AsyncStream { continuation in
        let listener = messageService.addListener { message in
            continuation.yield(message)
        }

        continuation.onTermination = { _ in
            messageService.removeListener(listener)
        }
    }
}

// Usage
for await message in observeMessages() {
    handleMessage(message)
}
```

## Timeout for Async Operations

Wrap external calls with timeout.

```swift
// Bad - no timeout
func fetchData() async throws -> Data {
    try await networkService.fetch()  // Could hang forever
}

// Good - explicit timeout
func fetchData() async throws -> Data {
    try await withThrowingTaskGroup(of: Data.self) { group in
        group.addTask {
            try await networkService.fetch()
        }

        group.addTask {
            try await Task.sleep(for: .seconds(30))
            throw TimeoutError()
        }

        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/async_patterns.md
git commit -m "feat(swift): add async_patterns.md with Swift concurrency patterns"
```

---

## Task 6: Create elements/error_handling.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/error_handling.md`

**Step 1: Write error_handling.md**

```markdown
# Error Handling

## Typed Error Enums

Define domain-specific error types conforming to Error.

```swift
// Bad - generic error
func fetchUser(id: Int) async throws -> User {
    guard id > 0 else {
        throw NSError(domain: "Invalid ID", code: -1)
    }
    // ...
}

// Good - typed domain error
enum UserError: Error {
    case invalidId(Int)
    case notFound(Int)
    case networkFailure(underlying: Error)
}

func fetchUser(id: Int) async throws -> User {
    guard id > 0 else {
        throw UserError.invalidId(id)
    }
    // ...
}
```

## LocalizedError for User-Facing Messages

Conform to LocalizedError when errors need display text.

```swift
enum OrderError: LocalizedError {
    case insufficientFunds(required: Decimal, available: Decimal)
    case itemOutOfStock(itemName: String)

    var errorDescription: String? {
        switch self {
        case .insufficientFunds(let required, let available):
            return "Insufficient funds. Required: \(required), Available: \(available)"
        case .itemOutOfStock(let name):
            return "\(name) is currently out of stock"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .insufficientFunds:
            return "Please add funds to your account"
        case .itemOutOfStock:
            return "Try again later or choose a different item"
        }
    }
}
```

## Result Type for Async Boundaries

Use Result at API boundaries when you need to capture success/failure without throwing.

```swift
// Good - Result for callbacks
func fetchUser(id: Int, completion: @escaping (Result<User, UserError>) -> Void) {
    Task {
        do {
            let user = try await userService.fetch(id: id)
            completion(.success(user))
        } catch let error as UserError {
            completion(.failure(error))
        } catch {
            completion(.failure(.networkFailure(underlying: error)))
        }
    }
}

// Good - Result in ViewModel for UI state
@Observable
final class UserViewModel {
    private(set) var result: Result<User, UserError>?

    func load(id: Int) async {
        do {
            let user = try await service.fetchUser(id: id)
            result = .success(user)
        } catch let error as UserError {
            result = .failure(error)
        } catch {
            result = .failure(.networkFailure(underlying: error))
        }
    }
}
```

## When to Throw vs Return Optional

Throw for unexpected failures. Return optional for expected "not found" cases.

```swift
// Good - optional for "not found" (expected case)
func findUser(byEmail email: String) async -> User? {
    // User may or may not exist - that's normal
}

// Good - throw for failures (unexpected case)
func fetchUser(id: Int) async throws -> User {
    // If we have an ID, the user should exist
    // Failure is exceptional
}

// Usage
if let user = await findUser(byEmail: email) {
    // Found
} else {
    // Not found - create account flow
}

do {
    let user = try await fetchUser(id: savedUserId)
} catch {
    // Something went wrong - show error
}
```

## Guard for Early Exit

Use guard to validate preconditions and exit early.

```swift
// Bad - nested conditionals
func processOrder(_ order: Order?) async throws -> Receipt {
    if let order = order {
        if order.items.isEmpty == false {
            if order.validated {
                return try await submitOrder(order)
            } else {
                throw OrderError.notValidated
            }
        } else {
            throw OrderError.emptyOrder
        }
    } else {
        throw OrderError.missingOrder
    }
}

// Good - guard for early exit
func processOrder(_ order: Order?) async throws -> Receipt {
    guard let order else {
        throw OrderError.missingOrder
    }

    guard !order.items.isEmpty else {
        throw OrderError.emptyOrder
    }

    guard order.validated else {
        throw OrderError.notValidated
    }

    return try await submitOrder(order)
}
```

## Do-Catch Specificity

Catch specific errors before generic ones.

```swift
// Bad - catches everything the same way
do {
    try await processPayment()
} catch {
    showError("Something went wrong")
}

// Good - specific handling per error type
do {
    try await processPayment()
} catch PaymentError.insufficientFunds {
    showFundsAlert()
} catch PaymentError.cardDeclined(let reason) {
    showCardError(reason)
} catch is NetworkError {
    showRetryOption()
} catch {
    showGenericError(error)
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/error_handling.md
git commit -m "feat(swift): add error_handling.md with typed errors and guard patterns"
```

---

## Task 7: Create elements/naming.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/naming.md`

**Step 1: Write naming.md**

```markdown
# Naming Rules

## No "is" Prefix for Boolean Adjectives

If the name reads as boolean without a prefix, skip the prefix. This diverges from Apple convention but reduces noise.

```swift
// Awkward - "is" adds nothing
var isLoading = true      // "loading" is already boolean
var isVisible = false     // "visible" is already boolean
var isEmpty: Bool { ... } // "empty" is already boolean

// Good - adjectives work without prefix
var loading = true
var visible = false
var empty: Bool { items.count == 0 }
var enabled = true
var selected = false

// Good - verb prefixes that form natural questions
func hasPermission() -> Bool     // "has permission?" - natural
func shouldRetry() -> Bool       // "should retry?" - natural
func canEdit() -> Bool           // "can edit?" - natural
func needsRefresh() -> Bool      // "needs refresh?" - natural
```

**Rule:** If the name reads as a yes/no question without a prefix, skip the prefix.

## Context Gives Meaning to Generic Names

Function context provides meaning. Generic names like `request`, `items`, `result` are clear when the function name establishes context.

```swift
// Good - function context makes generic names clear
func fetchUsers() async throws -> [User] {
    let request = buildRequest()     // Clearly a users request
    let items = try await send(request)  // Clearly user items
    return items.map { convert($0) }
}

// Bad - generic function + generic names = unclear
func process(_ data: Any) -> Any {
    let result = transform(data)    // What kind of result?
    let temp = validate(result)     // What are we validating?
    return temp
}
```

## Collection Plurals

Use plural names for collections. Use singular for individual items.

```swift
// Bad
let userList = fetchUsers()
for u in userList { ... }

// Good
let users = fetchUsers()
for user in users {
    process(user)
}
```

## Method Naming by Action

Method names should clearly indicate their action.

**Simple getters:** Use the noun directly, no prefix.

```swift
// Bad - redundant prefix
func getUser() -> User
func getConfig() -> Config

// Good - name is what it returns
var user: User { ... }
var config: Config { ... }
```

**Action methods:** Use clear verb prefixes.

| Prefix | Meaning | Example |
|--------|---------|---------|
| `fetch` | Retrieve from external source | `fetchUser()` |
| `create` | Create and return new instance | `createOrder()` |
| `build` | Construct from parts | `buildRequest()` |
| `parse` | Extract structure from raw | `parseResponse()` |
| `validate` | Check and return valid/throw | `validateInput()` |
| `convert` | Transform between types | `convertToDTO()` |
| `handle` | Process/react to something | `handleError()` |

## Protocol Naming

Protocols describe capability with `-able`, `-ing`, or noun.

```swift
// Good - capability suffix
protocol Fetchable { }
protocol Validating { }
protocol Logging { }

// Good - noun for role
protocol DataSource { }
protocol Delegate { }

// Bad - class-like naming
protocol UserManager { }  // Should be a concrete type
```

## Type Alias Names

Use PascalCase for type aliases. Make them descriptive.

```swift
// Good
typealias UserID = Int
typealias CompletionHandler = (Result<Data, Error>) -> Void
typealias JSON = [String: Any]
```

## Avoid Abbreviations

Use full words except for universally known abbreviations (URL, HTTP, ID, API).

```swift
// Bad
func usrInfo(usrId: Int) -> UsrData
func calcTtlAmt() -> Decimal

// Good
func userInfo(userId: Int) -> UserData
func calculateTotalAmount() -> Decimal

// OK - universal abbreviations
func fetchURL(_ url: URL) -> Data
func apiKey() -> String
```

## Constants

Use camelCase for constants (Swift convention), not SCREAMING_SNAKE_CASE.

```swift
// Swift convention
let defaultTimeout: TimeInterval = 30
let maxRetries = 3
let apiBaseURL = URL(string: "https://api.example.com")!

// Also acceptable for truly global constants
enum Constants {
    static let defaultPageSize = 20
    static let animationDuration: TimeInterval = 0.3
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/naming.md
git commit -m "feat(swift): add naming.md with no-is-prefix rule and Swift conventions"
```

---

## Task 8: Create elements/protocols.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/protocols.md`

**Step 1: Write protocols.md**

```markdown
# Protocols

## Protocol per Dependency Boundary

Define a protocol for each external dependency to enable testing.

```swift
// Bad - concrete dependency
class UserViewModel {
    private let service = UserService()  // Can't test in isolation
}

// Good - protocol at boundary
protocol UserServiceProtocol {
    func fetchUser(id: Int) async throws -> User
    func updateUser(_ user: User) async throws
}

class UserService: UserServiceProtocol {
    func fetchUser(id: Int) async throws -> User { ... }
    func updateUser(_ user: User) async throws { ... }
}

class UserViewModel {
    private let service: UserServiceProtocol

    init(service: UserServiceProtocol = UserService()) {
        self.service = service
    }
}
```

## Default Implementations via Extensions

Use protocol extensions to provide sensible defaults.

```swift
protocol Logging {
    var logPrefix: String { get }
    func log(_ message: String)
}

extension Logging {
    var logPrefix: String { String(describing: Self.self) }

    func log(_ message: String) {
        print("[\(logPrefix)] \(message)")
    }
}

// Types get default implementation automatically
struct OrderService: Logging {
    // logPrefix and log(_:) are provided
}

// Can override if needed
struct PaymentService: Logging {
    var logPrefix: String { "PAYMENT" }
    // Uses default log(_:)
}
```

## Protocol Composition

Combine protocols for flexible requirements.

```swift
// Define small, focused protocols
protocol Identifiable {
    var id: String { get }
}

protocol Timestamped {
    var createdAt: Date { get }
    var updatedAt: Date { get }
}

protocol Validatable {
    func validate() throws
}

// Compose as needed
func save<T: Identifiable & Timestamped>(_ item: T) { ... }

typealias Persistable = Identifiable & Timestamped & Codable
```

## Mocking for Tests

Create mock implementations conforming to protocols.

```swift
// Protocol
protocol NetworkClient {
    func fetch<T: Decodable>(_ url: URL) async throws -> T
}

// Production implementation
class URLSessionClient: NetworkClient {
    func fetch<T: Decodable>(_ url: URL) async throws -> T {
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(T.self, from: data)
    }
}

// Mock for testing
class MockNetworkClient: NetworkClient {
    var stubbedResult: Any?
    var stubbedError: Error?
    var fetchCallCount = 0
    var lastFetchedURL: URL?

    func fetch<T: Decodable>(_ url: URL) async throws -> T {
        fetchCallCount += 1
        lastFetchedURL = url

        if let error = stubbedError {
            throw error
        }

        return stubbedResult as! T
    }
}

// Test
func testFetchUser() async throws {
    let mock = MockNetworkClient()
    mock.stubbedResult = User(id: 1, name: "Test")

    let viewModel = UserViewModel(client: mock)
    await viewModel.loadUser(id: 1)

    XCTAssertEqual(mock.fetchCallCount, 1)
    XCTAssertEqual(viewModel.user?.name, "Test")
}
```

## Associated Types vs Generics

Use associated types when the type is determined by conformance. Use generics when the caller chooses.

```swift
// Associated type - conformer decides the type
protocol Repository {
    associatedtype Entity
    func fetch(id: String) async throws -> Entity
    func save(_ entity: Entity) async throws
}

class UserRepository: Repository {
    typealias Entity = User  // Repository decides
    func fetch(id: String) async throws -> User { ... }
    func save(_ entity: User) async throws { ... }
}

// Generic - caller decides the type
protocol Converter {
    func convert<T: Decodable>(from data: Data) throws -> T
}

class JSONConverter: Converter {
    func convert<T: Decodable>(from data: Data) throws -> T {
        try JSONDecoder().decode(T.self, from: data)
    }
}

// Caller chooses type
let user: User = try converter.convert(from: data)
let order: Order = try converter.convert(from: data)
```

## Protocol Witness Pattern

For testing static/global dependencies, use a protocol witness struct.

```swift
// Instead of mocking Date()
struct DateProvider {
    var now: () -> Date

    static let live = DateProvider { Date() }
    static let fixed = DateProvider { Date(timeIntervalSince1970: 0) }
}

class ExpirationChecker {
    private let dateProvider: DateProvider

    init(dateProvider: DateProvider = .live) {
        self.dateProvider = dateProvider
    }

    func isExpired(_ token: Token) -> Bool {
        token.expiresAt < dateProvider.now()
    }
}

// Test
func testExpiration() {
    let checker = ExpirationChecker(dateProvider: .fixed)
    // Deterministic test
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/protocols.md
git commit -m "feat(swift): add protocols.md with DI and mocking patterns"
```

---

## Task 9: Create elements/uikit_interop.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/uikit_interop.md`

**Step 1: Write uikit_interop.md**

```markdown
# UIKit Interop

## UIViewRepresentable Structure

Wrap UIKit views for use in SwiftUI.

```swift
struct MapView: UIViewRepresentable {
    let region: MKCoordinateRegion

    func makeUIView(context: Context) -> MKMapView {
        MKMapView()
    }

    func updateUIView(_ uiView: MKMapView, context: Context) {
        uiView.setRegion(region, animated: true)
    }
}
```

## Coordinator Pattern for Delegates

Use Coordinator to handle UIKit delegate callbacks.

```swift
struct ImagePicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker

        init(_ parent: ImagePicker) {
            self.parent = parent
        }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let image = info[.originalImage] as? UIImage {
                parent.selectedImage = image
            }
            parent.dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}
```

## UIViewControllerRepresentable for Full Screens

Wrap entire UIKit view controllers.

```swift
struct DocumentPicker: UIViewControllerRepresentable {
    let types: [UTType]
    let onPick: (URL) -> Void

    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: types)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIDocumentPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(onPick: onPick)
    }

    class Coordinator: NSObject, UIDocumentPickerDelegate {
        let onPick: (URL) -> Void

        init(onPick: @escaping (URL) -> Void) {
            self.onPick = onPick
        }

        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            if let url = urls.first {
                onPick(url)
            }
        }
    }
}
```

## When to Drop to UIKit

Use UIKit when SwiftUI lacks capability or has bugs.

**Good reasons to use UIKit:**
- Complex gestures (simultaneous recognition, custom gesture recognizers)
- Fine-grained scroll control (content offset, programmatic scrolling)
- Text fields with specific keyboard behavior
- Camera/media capture
- Existing UIKit components that work well

```swift
// Complex text input with UIKit
struct AdvancedTextField: UIViewRepresentable {
    @Binding var text: String
    let placeholder: String
    let onSubmit: () -> Void

    func makeUIView(context: Context) -> UITextField {
        let field = UITextField()
        field.placeholder = placeholder
        field.delegate = context.coordinator
        field.returnKeyType = .done
        field.autocorrectionType = .no
        return field
    }

    func updateUIView(_ uiView: UITextField, context: Context) {
        if uiView.text != text {
            uiView.text = text
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(text: $text, onSubmit: onSubmit)
    }

    class Coordinator: NSObject, UITextFieldDelegate {
        @Binding var text: String
        let onSubmit: () -> Void

        init(text: Binding<String>, onSubmit: @escaping () -> Void) {
            self._text = text
            self.onSubmit = onSubmit
        }

        func textFieldDidChangeSelection(_ textField: UITextField) {
            text = textField.text ?? ""
        }

        func textFieldShouldReturn(_ textField: UITextField) -> Bool {
            onSubmit()
            return true
        }
    }
}
```

## Avoiding Retain Cycles

Use `[weak self]` in closures and unowned references carefully.

```swift
// Bad - potential retain cycle
class Coordinator: NSObject {
    let parent: ImagePicker  // Strong reference

    func handleCompletion() {
        parent.completion(result)  // Parent holds coordinator, coordinator holds parent
    }
}

// Good - weak reference when appropriate
class Coordinator: NSObject {
    weak var parent: ImagePicker?

    func handleCompletion() {
        parent?.completion(result)
    }
}

// Or use closures instead of parent reference
class Coordinator: NSObject {
    let onComplete: (Result) -> Void

    init(onComplete: @escaping (Result) -> Void) {
        self.onComplete = onComplete
    }
}
```

## Hosting SwiftUI in UIKit

Use UIHostingController to embed SwiftUI views in UIKit.

```swift
// In a UIKit view controller
class LegacyViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()

        let swiftUIView = ModernView(viewModel: viewModel)
        let hostingController = UIHostingController(rootView: swiftUIView)

        addChild(hostingController)
        view.addSubview(hostingController.view)
        hostingController.view.frame = view.bounds
        hostingController.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        hostingController.didMove(toParent: self)
    }
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/uikit_interop.md
git commit -m "feat(swift): add uikit_interop.md with bridging patterns"
```

---

## Task 10: Create architecture/mvvm_swiftui.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/mvvm_swiftui.md`

**Step 1: Write mvvm_swiftui.md**

```markdown
# MVVM with SwiftUI

Model-View-ViewModel architecture for SwiftUI apps using @Observable.

## Directory Structure

```
App/
├── App.swift                      # App entry point
├── Core/                          # Shared domain logic
│   ├── Models/                    # Domain models
│   │   ├── User.swift
│   │   └── Order.swift
│   ├── Services/                  # Business logic services
│   │   ├── Protocols/
│   │   │   ├── UserServiceProtocol.swift
│   │   │   └── OrderServiceProtocol.swift
│   │   ├── UserService.swift
│   │   └── OrderService.swift
│   └── Utilities/
│       └── DateFormatter+Extensions.swift
│
├── Features/                      # Feature modules
│   ├── Auth/
│   │   ├── Views/
│   │   │   ├── LoginView.swift
│   │   │   └── SignupView.swift
│   │   └── ViewModels/
│   │       ├── LoginViewModel.swift
│   │       └── SignupViewModel.swift
│   │
│   ├── Home/
│   │   ├── Views/
│   │   │   ├── HomeView.swift
│   │   │   └── Components/
│   │   │       ├── UserCard.swift
│   │   │       └── ActivityFeed.swift
│   │   └── ViewModels/
│   │       └── HomeViewModel.swift
│   │
│   └── Profile/
│       ├── Views/
│       │   └── ProfileView.swift
│       └── ViewModels/
│           └── ProfileViewModel.swift
│
├── Shared/                        # Reusable UI components
│   ├── Components/
│   │   ├── LoadingView.swift
│   │   ├── ErrorView.swift
│   │   └── EmptyStateView.swift
│   └── Modifiers/
│       └── CardModifier.swift
│
└── Resources/
    ├── Assets.xcassets
    └── Localizable.strings
```

## ViewModel Pattern with @Observable

```swift
// Features/Profile/ViewModels/ProfileViewModel.swift
import SwiftUI

@MainActor
@Observable
final class ProfileViewModel {
    // MARK: - State
    private(set) var user: User?
    private(set) var loading = false
    private(set) var error: Error?

    // MARK: - Dependencies
    private let userService: UserServiceProtocol

    // MARK: - Init
    init(userService: UserServiceProtocol = UserService()) {
        self.userService = userService
    }

    // MARK: - Actions
    func loadProfile() async {
        loading = true
        error = nil

        do {
            user = try await userService.fetchCurrentUser()
        } catch {
            self.error = error
        }

        loading = false
    }

    func updateName(_ name: String) async {
        guard var currentUser = user else { return }
        currentUser.name = name

        do {
            user = try await userService.updateUser(currentUser)
        } catch {
            self.error = error
        }
    }
}
```

## View Binding Pattern

```swift
// Features/Profile/Views/ProfileView.swift
import SwiftUI

struct ProfileView: View {
    let viewModel: ProfileViewModel

    var body: some View {
        Group {
            if viewModel.loading {
                ProgressView()
            } else if let error = viewModel.error {
                ErrorView(error: error) {
                    Task { await viewModel.loadProfile() }
                }
            } else if let user = viewModel.user {
                ProfileContent(user: user)
            }
        }
        .navigationTitle("Profile")
        .task {
            await viewModel.loadProfile()
        }
    }
}

private struct ProfileContent: View {
    let user: User

    var body: some View {
        List {
            Section("Personal") {
                LabeledContent("Name", value: user.name)
                LabeledContent("Email", value: user.email)
            }
        }
    }
}
```

## Lifecycle Management

Use `.task` for async initialization - it cancels automatically on disappear.

```swift
struct UserListView: View {
    let viewModel: UserListViewModel

    var body: some View {
        List(viewModel.users) { user in
            UserRow(user: user)
        }
        .task {
            // Loads when view appears
            // Automatically cancelled when view disappears
            await viewModel.loadUsers()
        }
        .refreshable {
            // Pull to refresh
            await viewModel.loadUsers()
        }
    }
}
```

## State Enum for Complex Screens

```swift
@MainActor
@Observable
final class DataViewModel {
    enum State {
        case idle
        case loading
        case loaded([Item])
        case empty
        case error(Error)
    }

    private(set) var state: State = .idle

    private let service: DataServiceProtocol

    init(service: DataServiceProtocol = DataService()) {
        self.service = service
    }

    func load() async {
        state = .loading

        do {
            let items = try await service.fetchItems()
            state = items.isEmpty ? .empty : .loaded(items)
        } catch {
            state = .error(error)
        }
    }
}

struct DataView: View {
    let viewModel: DataViewModel

    var body: some View {
        content
            .task { await viewModel.load() }
    }

    @ViewBuilder
    private var content: some View {
        switch viewModel.state {
        case .idle, .loading:
            ProgressView()
        case .loaded(let items):
            ItemList(items: items)
        case .empty:
            EmptyStateView(message: "No items found")
        case .error(let error):
            ErrorView(error: error) {
                Task { await viewModel.load() }
            }
        }
    }
}
```

## Testing ViewModels

```swift
@MainActor
final class ProfileViewModelTests: XCTestCase {
    func testLoadProfile_success() async {
        // Given
        let mockService = MockUserService()
        mockService.stubbedUser = User(id: 1, name: "Test", email: "test@example.com")
        let viewModel = ProfileViewModel(userService: mockService)

        // When
        await viewModel.loadProfile()

        // Then
        XCTAssertFalse(viewModel.loading)
        XCTAssertNil(viewModel.error)
        XCTAssertEqual(viewModel.user?.name, "Test")
    }

    func testLoadProfile_failure() async {
        // Given
        let mockService = MockUserService()
        mockService.stubbedError = NetworkError.noConnection
        let viewModel = ProfileViewModel(userService: mockService)

        // When
        await viewModel.loadProfile()

        // Then
        XCTAssertFalse(viewModel.loading)
        XCTAssertNotNil(viewModel.error)
        XCTAssertNil(viewModel.user)
    }
}
```

## Benefits

1. **Testability** - ViewModels are plain Swift classes, easy to test in isolation
2. **Separation** - Views only describe UI, ViewModels handle logic
3. **Reusability** - ViewModels can be shared across views if needed
4. **Predictability** - State flows one direction (ViewModel → View)
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/mvvm_swiftui.md
git commit -m "feat(swift): add mvvm_swiftui.md with @Observable architecture"
```

---

## Task 11: Create architecture/navigation.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/navigation.md`

**Step 1: Write navigation.md**

```markdown
# Navigation Patterns

Navigation in SwiftUI using NavigationStack with type-safe routing.

## NavigationStack with Path

Use NavigationStack with a path for programmatic navigation.

```swift
// Define navigation destinations
enum Route: Hashable {
    case userDetail(userId: Int)
    case settings
    case orderHistory
    case orderDetail(orderId: String)
}

struct ContentView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            HomeView(path: $path)
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .userDetail(let userId):
                        UserDetailView(userId: userId)
                    case .settings:
                        SettingsView()
                    case .orderHistory:
                        OrderHistoryView(path: $path)
                    case .orderDetail(let orderId):
                        OrderDetailView(orderId: orderId)
                    }
                }
        }
    }
}

// Navigate programmatically
struct HomeView: View {
    @Binding var path: NavigationPath

    var body: some View {
        List {
            Button("View Profile") {
                path.append(Route.userDetail(userId: 123))
            }
            Button("Settings") {
                path.append(Route.settings)
            }
        }
    }
}
```

## Deep Linking

Support deep links by parsing URLs into navigation paths.

```swift
@MainActor
@Observable
final class NavigationManager {
    var path = NavigationPath()

    func handleDeepLink(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let host = components.host else {
            return
        }

        // Reset to root
        path = NavigationPath()

        // Parse path and navigate
        switch host {
        case "user":
            if let userId = components.queryItems?.first(where: { $0.name == "id" })?.value,
               let id = Int(userId) {
                path.append(Route.userDetail(userId: id))
            }
        case "order":
            if let orderId = components.queryItems?.first(where: { $0.name == "id" })?.value {
                path.append(Route.orderHistory)
                path.append(Route.orderDetail(orderId: orderId))
            }
        default:
            break
        }
    }
}

// App entry point
@main
struct MyApp: App {
    @State private var navigationManager = NavigationManager()

    var body: some Scene {
        WindowGroup {
            ContentView(path: $navigationManager.path)
                .onOpenURL { url in
                    navigationManager.handleDeepLink(url)
                }
        }
    }
}
```

## Sheet and FullScreen Presentation

Use separate state for modal presentation.

```swift
struct ProfileView: View {
    @State private var showingSettings = false
    @State private var showingEditProfile = false

    var body: some View {
        List {
            Button("Edit Profile") {
                showingEditProfile = true
            }
            Button("Settings") {
                showingSettings = true
            }
        }
        .sheet(isPresented: $showingEditProfile) {
            EditProfileView()
        }
        .fullScreenCover(isPresented: $showingSettings) {
            SettingsView()
        }
    }
}
```

## Item-Based Presentation

Present sheets based on identifiable items.

```swift
struct OrderListView: View {
    @State private var selectedOrder: Order?
    let orders: [Order]

    var body: some View {
        List(orders) { order in
            Button(order.title) {
                selectedOrder = order
            }
        }
        .sheet(item: $selectedOrder) { order in
            OrderDetailView(order: order)
        }
    }
}
```

## Coordinator Pattern for Complex Flows

For multi-step flows, use a coordinator pattern.

```swift
@MainActor
@Observable
final class OnboardingCoordinator {
    enum Step: Hashable {
        case welcome
        case profile
        case preferences
        case complete
    }

    private(set) var currentStep: Step = .welcome
    var completed = false

    func next() {
        switch currentStep {
        case .welcome:
            currentStep = .profile
        case .profile:
            currentStep = .preferences
        case .preferences:
            currentStep = .complete
        case .complete:
            completed = true
        }
    }

    func back() {
        switch currentStep {
        case .welcome:
            break
        case .profile:
            currentStep = .welcome
        case .preferences:
            currentStep = .profile
        case .complete:
            currentStep = .preferences
        }
    }
}

struct OnboardingFlow: View {
    @State private var coordinator = OnboardingCoordinator()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            content
                .toolbar {
                    if coordinator.currentStep != .welcome {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Back") { coordinator.back() }
                        }
                    }
                }
        }
        .onChange(of: coordinator.completed) { _, completed in
            if completed { dismiss() }
        }
    }

    @ViewBuilder
    private var content: some View {
        switch coordinator.currentStep {
        case .welcome:
            WelcomeStep(onNext: { coordinator.next() })
        case .profile:
            ProfileStep(onNext: { coordinator.next() })
        case .preferences:
            PreferencesStep(onNext: { coordinator.next() })
        case .complete:
            CompleteStep(onNext: { coordinator.next() })
        }
    }
}
```

## Navigation State Persistence

Save and restore navigation state across app launches.

```swift
@MainActor
@Observable
final class NavigationManager {
    var path = NavigationPath()

    private let persistenceKey = "navigation_path"

    init() {
        loadPersistedPath()
    }

    func save() {
        guard let data = try? JSONEncoder().encode(path.codable) else { return }
        UserDefaults.standard.set(data, forKey: persistenceKey)
    }

    private func loadPersistedPath() {
        guard let data = UserDefaults.standard.data(forKey: persistenceKey),
              let decoded = try? JSONDecoder().decode(
                NavigationPath.CodableRepresentation.self,
                from: data
              ) else {
            return
        }
        path = NavigationPath(decoded)
    }
}

// Save on scene phase change
struct ContentView: View {
    @State private var navigationManager = NavigationManager()
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack(path: $navigationManager.path) {
            // ...
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .inactive {
                navigationManager.save()
            }
        }
    }
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/navigation.md
git commit -m "feat(swift): add navigation.md with NavigationStack and deep linking"
```

---

## Task 12: Create architecture/dependency_injection.md

**Files:**
- Create: `plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/dependency_injection.md`

**Step 1: Write dependency_injection.md**

```markdown
# Dependency Injection

Strategies for injecting dependencies in SwiftUI apps.

## Protocol at Boundaries

Define protocols for external dependencies.

```swift
// Core/Services/Protocols/UserServiceProtocol.swift
protocol UserServiceProtocol {
    func fetchUser(id: Int) async throws -> User
    func updateUser(_ user: User) async throws -> User
    func deleteUser(id: Int) async throws
}

// Core/Services/UserService.swift
final class UserService: UserServiceProtocol {
    private let networkClient: NetworkClient

    init(networkClient: NetworkClient = URLSessionClient()) {
        self.networkClient = networkClient
    }

    func fetchUser(id: Int) async throws -> User {
        try await networkClient.get("/users/\(id)")
    }

    func updateUser(_ user: User) async throws -> User {
        try await networkClient.put("/users/\(user.id)", body: user)
    }

    func deleteUser(id: Int) async throws {
        try await networkClient.delete("/users/\(id)")
    }
}
```

## Initializer Injection for ViewModels

Inject dependencies through ViewModel initializers.

```swift
@MainActor
@Observable
final class ProfileViewModel {
    private let userService: UserServiceProtocol
    private let analyticsService: AnalyticsServiceProtocol

    // Production initializer with defaults
    init(
        userService: UserServiceProtocol = UserService(),
        analyticsService: AnalyticsServiceProtocol = AnalyticsService()
    ) {
        self.userService = userService
        self.analyticsService = analyticsService
    }

    func loadProfile() async {
        analyticsService.track(.profileViewed)
        // ...
    }
}

// Test with mocks
let viewModel = ProfileViewModel(
    userService: MockUserService(),
    analyticsService: MockAnalyticsService()
)
```

## Environment for View-Level Dependencies

Use SwiftUI Environment for dependencies needed by views.

```swift
// Define environment key
struct UserServiceKey: EnvironmentKey {
    static let defaultValue: UserServiceProtocol = UserService()
}

extension EnvironmentValues {
    var userService: UserServiceProtocol {
        get { self[UserServiceKey.self] }
        set { self[UserServiceKey.self] = newValue }
    }
}

// Inject at app root
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.userService, UserService())
        }
    }
}

// Use in views
struct ProfileView: View {
    @Environment(\.userService) private var userService

    var body: some View {
        // Can pass to ViewModel or use directly for simple cases
    }
}
```

## Dependency Container

For complex apps, use a container to manage dependencies.

```swift
@MainActor
@Observable
final class Dependencies {
    // Services
    let userService: UserServiceProtocol
    let orderService: OrderServiceProtocol
    let analyticsService: AnalyticsServiceProtocol

    // Shared state
    let authManager: AuthManager

    init(
        userService: UserServiceProtocol = UserService(),
        orderService: OrderServiceProtocol = OrderService(),
        analyticsService: AnalyticsServiceProtocol = AnalyticsService(),
        authManager: AuthManager = AuthManager()
    ) {
        self.userService = userService
        self.orderService = orderService
        self.analyticsService = analyticsService
        self.authManager = authManager
    }

    // Factory methods for ViewModels
    func makeProfileViewModel() -> ProfileViewModel {
        ProfileViewModel(
            userService: userService,
            analyticsService: analyticsService
        )
    }

    func makeOrderViewModel() -> OrderViewModel {
        OrderViewModel(
            orderService: orderService,
            userService: userService
        )
    }
}

// Inject container via environment
struct DependenciesKey: EnvironmentKey {
    static let defaultValue = Dependencies()
}

extension EnvironmentValues {
    var dependencies: Dependencies {
        get { self[DependenciesKey.self] }
        set { self[DependenciesKey.self] = newValue }
    }
}

// Use in views
struct ProfileView: View {
    @Environment(\.dependencies) private var deps
    @State private var viewModel: ProfileViewModel?

    var body: some View {
        Group {
            if let viewModel {
                ProfileContent(viewModel: viewModel)
            } else {
                ProgressView()
            }
        }
        .task {
            viewModel = deps.makeProfileViewModel()
        }
    }
}
```

## Preview Configuration

Create preview-specific dependencies.

```swift
extension Dependencies {
    static let preview = Dependencies(
        userService: PreviewUserService(),
        orderService: PreviewOrderService(),
        analyticsService: NoOpAnalyticsService(),
        authManager: PreviewAuthManager()
    )
}

struct PreviewUserService: UserServiceProtocol {
    func fetchUser(id: Int) async throws -> User {
        User(id: id, name: "Preview User", email: "preview@example.com")
    }

    func updateUser(_ user: User) async throws -> User {
        user
    }

    func deleteUser(id: Int) async throws {}
}

// In previews
#Preview {
    ProfileView()
        .environment(\.dependencies, .preview)
}
```

## Testing Configuration

Create test mocks with verification capabilities.

```swift
final class MockUserService: UserServiceProtocol {
    var fetchUserResult: Result<User, Error> = .success(User.mock)
    var fetchCallCount = 0
    var lastFetchedId: Int?

    func fetchUser(id: Int) async throws -> User {
        fetchCallCount += 1
        lastFetchedId = id
        return try fetchUserResult.get()
    }

    // ... other methods
}

// Test
@MainActor
final class ProfileViewModelTests: XCTestCase {
    func testLoadProfile() async {
        let mockService = MockUserService()
        mockService.fetchUserResult = .success(User(id: 1, name: "Test", email: "test@test.com"))

        let viewModel = ProfileViewModel(userService: mockService)
        await viewModel.loadProfile()

        XCTAssertEqual(mockService.fetchCallCount, 1)
        XCTAssertEqual(viewModel.user?.name, "Test")
    }
}
```

## Lazy Initialization

Defer expensive initialization until first use.

```swift
@MainActor
@Observable
final class Dependencies {
    // Lazy services
    private var _databaseService: DatabaseService?
    var databaseService: DatabaseService {
        if _databaseService == nil {
            _databaseService = DatabaseService()
        }
        return _databaseService!
    }

    // Or use lazy var for simpler cases
    lazy var heavyService = HeavyService()
}
```
```

**Step 2: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/dependency_injection.md
git commit -m "feat(swift): add dependency_injection.md with Environment and container patterns"
```

---

## Task 13: Update navigation-map.md

**Files:**
- Modify: `plugins/refactoring-guru/skills/refactoring-guide/references/navigation-map.md`

**Step 1: Read current file**

Use Read tool to get current content.

**Step 2: Update navigation-map.md with Swift entries**

Replace the entire file with updated content that includes Swift in:
- Structure tree
- File Descriptions section with Swift subsection
- Elements table with Swift row
- Architecture table with Swift row
- Quick Reference table with Swift scenarios

**Step 3: Commit**

```bash
git add plugins/refactoring-guru/skills/refactoring-guide/references/navigation-map.md
git commit -m "feat(swift): update navigation-map.md with Swift language entries"
```

---

## Task 14: Final Verification

**Step 1: Verify directory structure**

```bash
find plugins/refactoring-guru/skills/refactoring-guide/references/swift -type f -name "*.md" | sort
```

Expected output:
```
plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/dependency_injection.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/mvvm_swiftui.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/architecture/navigation.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/async_patterns.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/error_handling.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/naming.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/protocols.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/uikit_interop.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/view_structure.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/elements/viewmodel_design.md
plugins/refactoring-guru/skills/refactoring-guide/references/swift/principles.md
```

**Step 2: Verify file count**

```bash
find plugins/refactoring-guru/skills/refactoring-guide/references/swift -type f -name "*.md" | wc -l
```

Expected: 11

**Step 3: Final commit with summary**

```bash
git log --oneline -15
```

Verify all Swift-related commits are present.
