# Protocols

## Protocol per Dependency Boundary

Define a protocol for each external dependency to enable testing and flexibility. Concrete dependencies hardcoded in types prevent mocking and create tight coupling.

```swift
// Bad - concrete dependency prevents testing
@Observable
class ProfileViewModel {
    private let userService = UserService()
    private let analytics = AnalyticsService()
    private(set) var user: User?

    func loadProfile() async {
        user = try? await userService.fetchCurrentUser()
        analytics.track(.profileViewed)
    }
}

// Tests require real network calls and analytics events

// Good - protocol boundaries enable injection
protocol UserServiceProtocol {
    func fetchCurrentUser() async throws -> User
}

protocol AnalyticsProtocol {
    func track(_ event: AnalyticsEvent)
}

@Observable
class ProfileViewModel {
    private let userService: UserServiceProtocol
    private let analytics: AnalyticsProtocol
    private(set) var user: User?

    init(
        userService: UserServiceProtocol = UserService(),
        analytics: AnalyticsProtocol = AnalyticsService()
    ) {
        self.userService = userService
        self.analytics = analytics
    }

    func loadProfile() async {
        user = try? await userService.fetchCurrentUser()
        analytics.track(.profileViewed)
    }
}

// Production implementations
class UserService: UserServiceProtocol {
    func fetchCurrentUser() async throws -> User {
        // Real network call
    }
}

class AnalyticsService: AnalyticsProtocol {
    func track(_ event: AnalyticsEvent) {
        // Real analytics SDK
    }
}

// Test with mocks
func testProfileLoadsUser() async {
    let mockUser = MockUserService()
    mockUser.userToReturn = User(name: "Test")
    let viewModel = ProfileViewModel(
        userService: mockUser,
        analytics: MockAnalytics()
    )

    await viewModel.loadProfile()

    XCTAssertEqual(viewModel.user?.name, "Test")
}
```

## Default Implementations via Extensions

Use protocol extensions to provide sensible defaults. Types get behavior automatically but can override when needed. This reduces boilerplate while maintaining flexibility.

```swift
// Bad - every conforming type must implement everything
protocol Logging {
    var logPrefix: String { get }
    func log(_ message: String)
}

struct OrderService: Logging {
    var logPrefix: String { "OrderService" }

    func log(_ message: String) {
        print("[\(logPrefix)] \(message)")
    }

    func createOrder() {
        log("Creating order")
    }
}

struct PaymentService: Logging {
    var logPrefix: String { "PaymentService" }

    // Same implementation, repeated
    func log(_ message: String) {
        print("[\(logPrefix)] \(message)")
    }

    func processPayment() {
        log("Processing payment")
    }
}

// Good - extension provides defaults
protocol Logging {
    var logPrefix: String { get }
    func log(_ message: String)
}

extension Logging {
    var logPrefix: String {
        String(describing: Self.self)
    }

    func log(_ message: String) {
        print("[\(logPrefix)] \(message)")
    }
}

// Gets defaults automatically
struct OrderService: Logging {
    func createOrder() {
        log("Creating order")  // Uses default prefix "OrderService"
    }
}

// Can override when needed
struct PaymentService: Logging {
    var logPrefix: String { "Payments" }  // Custom prefix

    func processPayment() {
        log("Processing payment")  // Logs as "[Payments] Processing payment"
    }
}

// Can override both
struct AuditService: Logging {
    var logPrefix: String { "AUDIT" }

    func log(_ message: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        print("[\(timestamp)][\(logPrefix)] \(message)")
    }
}
```

## Protocol Composition

Combine small, focused protocols for flexible requirements. Large protocols force types to implement irrelevant methods. Composition with `&` creates precise requirements.

```swift
// Bad - monolithic protocol
protocol Entity {
    var id: UUID { get }
    var createdAt: Date { get }
    var updatedAt: Date { get }
    func validate() throws
    func encode() throws -> Data
    func save() async throws
    func delete() async throws
}

// Every entity must implement everything, even if not needed
struct ReadOnlyMetric: Entity {
    let id: UUID
    let createdAt: Date
    let updatedAt: Date
    let value: Double

    func validate() throws { }  // Not relevant
    func encode() throws -> Data { Data() }  // Not relevant
    func save() async throws { fatalError() }  // Should never be called
    func delete() async throws { fatalError() }  // Should never be called
}

// Good - small focused protocols
protocol Identifiable {
    var id: UUID { get }
}

protocol Timestamped {
    var createdAt: Date { get }
    var updatedAt: Date { get }
}

protocol Validatable {
    func validate() throws
}

protocol Persistable {
    func save() async throws
    func delete() async throws
}

// Compose what you need
typealias StorableEntity = Identifiable & Timestamped & Codable & Persistable

struct User: StorableEntity {
    let id: UUID
    let createdAt: Date
    var updatedAt: Date
    var name: String

    func save() async throws { }
    func delete() async throws { }
}

// Read-only type only conforms to what it needs
struct ReadOnlyMetric: Identifiable, Timestamped, Codable {
    let id: UUID
    let createdAt: Date
    let updatedAt: Date
    let value: Double
}

// Functions require exactly what they need
func persist<T: Identifiable & Persistable>(_ item: T) async throws {
    print("Saving item \(item.id)")
    try await item.save()
}

func archive<T: Timestamped & Codable>(_ item: T) throws -> Data {
    try JSONEncoder().encode(item)
}
```

## Mocking for Tests

Create mock implementations that conform to protocols. Mocks can stub results, track calls, and verify interactions without external dependencies.

```swift
// Production implementation
protocol NetworkClientProtocol {
    func fetch(url: URL) async throws -> Data
}

class URLSessionClient: NetworkClientProtocol {
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func fetch(url: URL) async throws -> Data {
        let (data, _) = try await session.data(from: url)
        return data
    }
}

// Mock for testing
class MockNetworkClient: NetworkClientProtocol {
    // Stubbed result
    var dataToReturn: Data = Data()
    var errorToThrow: Error?

    // Call tracking
    var fetchCallCount = 0
    var lastFetchedURL: URL?

    func fetch(url: URL) async throws -> Data {
        fetchCallCount += 1
        lastFetchedURL = url

        if let error = errorToThrow {
            throw error
        }
        return dataToReturn
    }
}

// Usage in tests
func testFetchesFromCorrectURL() async throws {
    let mock = MockNetworkClient()
    mock.dataToReturn = """
        {"users": [{"name": "Alice"}]}
        """.data(using: .utf8)!

    let service = UserService(client: mock)

    _ = try await service.fetchUsers()

    XCTAssertEqual(mock.fetchCallCount, 1)
    XCTAssertEqual(mock.lastFetchedURL?.path, "/api/users")
}

func testHandlesNetworkError() async {
    let mock = MockNetworkClient()
    mock.errorToThrow = URLError(.notConnectedToInternet)

    let viewModel = UserListViewModel(
        service: UserService(client: mock)
    )

    await viewModel.loadUsers()

    XCTAssertTrue(viewModel.users.isEmpty)
    XCTAssertNotNil(viewModel.error)
}
```

## Associated Types vs Generics

Use associated types when the conforming type decides the type. Use generics when the caller decides. This distinction determines where the type choice lives.

```swift
// Associated type - conformer decides the type
protocol Repository {
    associatedtype Entity

    func fetch(id: UUID) async throws -> Entity?
    func save(_ entity: Entity) async throws
    func delete(id: UUID) async throws
}

// The repository implementation chooses what Entity is
class UserRepository: Repository {
    typealias Entity = User

    func fetch(id: UUID) async throws -> User? {
        // Fetch User from database
    }

    func save(_ entity: User) async throws {
        // Save User to database
    }

    func delete(id: UUID) async throws {
        // Delete User from database
    }
}

class OrderRepository: Repository {
    typealias Entity = Order

    func fetch(id: UUID) async throws -> Order? { }
    func save(_ entity: Order) async throws { }
    func delete(id: UUID) async throws { }
}

// Generic - caller decides the type
protocol Decoder {
    func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T
}

class JSONParser: Decoder {
    func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
        try JSONDecoder().decode(type, from: data)
    }
}

// Caller chooses the type at call site
let parser = JSONParser()
let user = try parser.decode(User.self, from: userData)
let order = try parser.decode(Order.self, from: orderData)

// Combining both - associated type with generic method
protocol Cache {
    associatedtype Key: Hashable

    func get<Value: Codable>(_ key: Key) -> Value?
    func set<Value: Codable>(_ value: Value, for key: Key)
}

class StringKeyCache: Cache {
    typealias Key = String
    private var storage: [String: Data] = [:]

    func get<Value: Codable>(_ key: String) -> Value? {
        guard let data = storage[key] else { return nil }
        return try? JSONDecoder().decode(Value.self, from: data)
    }

    func set<Value: Codable>(_ value: Value, for key: String) {
        storage[key] = try? JSONEncoder().encode(value)
    }
}

// Key type fixed by conformer, Value type chosen by caller
let cache = StringKeyCache()
cache.set(user, for: "current-user")
let cached: User? = cache.get("current-user")
```

## Protocol Witness Pattern

For testing static or global dependencies like `Date()` or `UUID()`, use a protocol witness struct. This provides a testable seam without the overhead of protocol conformance.

```swift
// Bad - untestable global dependency
class TokenManager {
    func isTokenExpired(_ token: Token) -> Bool {
        token.expiresAt < Date()  // Untestable - Date() is non-deterministic
    }

    func generateRefreshToken() -> RefreshToken {
        RefreshToken(
            id: UUID(),  // Untestable - UUID() is random
            issuedAt: Date()
        )
    }
}

// Tests are flaky or impossible
func testTokenExpiry() {
    let token = Token(expiresAt: Date().addingTimeInterval(60))
    let manager = TokenManager()
    XCTAssertFalse(manager.isTokenExpired(token))  // Race condition!
}

// Good - protocol witness for dependencies
struct DateProvider {
    var now: () -> Date

    static let live = DateProvider { Date() }

    static func fixed(_ date: Date) -> DateProvider {
        DateProvider { date }
    }
}

struct UUIDProvider {
    var generate: () -> UUID

    static let live = UUIDProvider { UUID() }

    static func fixed(_ uuid: UUID) -> UUIDProvider {
        UUIDProvider { uuid }
    }

    static func sequential(startingAt start: Int = 0) -> UUIDProvider {
        var counter = start
        return UUIDProvider {
            defer { counter += 1 }
            return UUID(uuidString: "00000000-0000-0000-0000-\(String(format: "%012d", counter))")!
        }
    }
}

class TokenManager {
    private let dateProvider: DateProvider
    private let uuidProvider: UUIDProvider

    init(
        dateProvider: DateProvider = .live,
        uuidProvider: UUIDProvider = .live
    ) {
        self.dateProvider = dateProvider
        self.uuidProvider = uuidProvider
    }

    func isTokenExpired(_ token: Token) -> Bool {
        token.expiresAt < dateProvider.now()
    }

    func generateRefreshToken() -> RefreshToken {
        RefreshToken(
            id: uuidProvider.generate(),
            issuedAt: dateProvider.now()
        )
    }
}

// Deterministic tests
func testTokenNotExpiredBeforeExpiryTime() {
    let fixedNow = Date(timeIntervalSince1970: 1000)
    let manager = TokenManager(dateProvider: .fixed(fixedNow))

    let token = Token(expiresAt: Date(timeIntervalSince1970: 1060))

    XCTAssertFalse(manager.isTokenExpired(token))
}

func testTokenExpiredAfterExpiryTime() {
    let fixedNow = Date(timeIntervalSince1970: 1100)
    let manager = TokenManager(dateProvider: .fixed(fixedNow))

    let token = Token(expiresAt: Date(timeIntervalSince1970: 1060))

    XCTAssertTrue(manager.isTokenExpired(token))
}

func testRefreshTokenGeneration() {
    let fixedDate = Date(timeIntervalSince1970: 1000)
    let fixedUUID = UUID(uuidString: "12345678-1234-1234-1234-123456789012")!

    let manager = TokenManager(
        dateProvider: .fixed(fixedDate),
        uuidProvider: .fixed(fixedUUID)
    )

    let token = manager.generateRefreshToken()

    XCTAssertEqual(token.id, fixedUUID)
    XCTAssertEqual(token.issuedAt, fixedDate)
}
```
