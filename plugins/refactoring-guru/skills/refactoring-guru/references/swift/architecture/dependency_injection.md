# Dependency Injection in Swift

Dependency injection enables testable, modular code by providing dependencies from outside rather than creating them internally. Swift offers multiple patterns suited to different scenarios, from simple initializer injection to SwiftUI's environment system.

## Protocol at Boundaries

Define protocols for external dependencies to enable substitution during testing and facilitate loose coupling.

```swift
// Core/Services/Protocols/UserServiceProtocol.swift
protocol UserServiceProtocol: Sendable {
    func fetchUser(id: UUID) async throws -> User
    func updateUser(_ user: User) async throws -> User
    func deleteUser(id: UUID) async throws
}

// Core/Services/Protocols/AnalyticsServiceProtocol.swift
protocol AnalyticsServiceProtocol: Sendable {
    func track(event: String, properties: [String: Any])
    func identify(userId: String)
    func reset()
}
```

```swift
// Core/Services/UserService.swift
final class UserService: UserServiceProtocol {
    private let networkService: NetworkServiceProtocol

    init(networkService: NetworkServiceProtocol) {
        self.networkService = networkService
    }

    func fetchUser(id: UUID) async throws -> User {
        try await networkService.request(
            endpoint: .user(id: id),
            responseType: User.self
        )
    }

    func updateUser(_ user: User) async throws -> User {
        try await networkService.request(
            endpoint: .updateUser(user),
            responseType: User.self
        )
    }

    func deleteUser(id: UUID) async throws {
        try await networkService.request(endpoint: .deleteUser(id: id))
    }
}
```

```swift
// Core/Services/AnalyticsService.swift
final class AnalyticsService: AnalyticsServiceProtocol {
    private let apiKey: String

    init(apiKey: String) {
        self.apiKey = apiKey
    }

    func track(event: String, properties: [String: Any]) {
        // Send to analytics backend
    }

    func identify(userId: String) {
        // Identify user in analytics
    }

    func reset() {
        // Clear analytics state
    }
}
```

**Key aspects:**

- Protocols marked `Sendable` for safe use with Swift Concurrency
- Each protocol defines a focused set of related operations
- Implementations receive their own dependencies through initializers

## Initializer Injection for ViewModels

Inject dependencies through the initializer with default values for production use.

```swift
// Features/Profile/ViewModels/ProfileViewModel.swift
import Foundation

@MainActor
@Observable
final class ProfileViewModel {

    // MARK: - State

    private(set) var user: User?
    private(set) var isLoading = false
    private(set) var error: Error?

    // MARK: - Dependencies

    private let userService: UserServiceProtocol
    private let analyticsService: AnalyticsServiceProtocol

    // MARK: - Init

    init(
        userService: UserServiceProtocol = UserService(networkService: NetworkService()),
        analyticsService: AnalyticsServiceProtocol = AnalyticsService(apiKey: Config.analyticsKey)
    ) {
        self.userService = userService
        self.analyticsService = analyticsService
    }

    // MARK: - Actions

    func loadProfile(userId: UUID) async {
        isLoading = true
        error = nil
        analyticsService.track(event: "profile_load_started", properties: ["user_id": userId.uuidString])

        do {
            user = try await userService.fetchUser(id: userId)
            analyticsService.track(event: "profile_load_success", properties: [:])
        } catch {
            self.error = error
            analyticsService.track(event: "profile_load_error", properties: ["error": error.localizedDescription])
        }

        isLoading = false
    }

    func updateProfile(name: String, email: String) async {
        guard var currentUser = user else { return }

        currentUser.name = name
        currentUser.email = email
        isLoading = true

        do {
            user = try await userService.updateUser(currentUser)
            analyticsService.track(event: "profile_updated", properties: [:])
        } catch {
            self.error = error
        }

        isLoading = false
    }
}
```

**Key aspects:**

- Default parameters provide production implementations
- Tests can inject mocks without modifying the ViewModel
- Dependencies are stored as protocol types for flexibility

## Environment for View-Level Dependencies

SwiftUI's environment system propagates dependencies through the view hierarchy.

### Define Environment Key

```swift
// Core/Environment/UserServiceKey.swift
import SwiftUI

private struct UserServiceKey: EnvironmentKey {
    static let defaultValue: UserServiceProtocol = UserService(
        networkService: NetworkService()
    )
}

extension EnvironmentValues {
    var userService: UserServiceProtocol {
        get { self[UserServiceKey.self] }
        set { self[UserServiceKey.self] = newValue }
    }
}
```

### Inject at App Root

```swift
// MyApp.swift
import SwiftUI

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.userService, UserService(networkService: NetworkService()))
        }
    }
}
```

### Use in Views

```swift
// Features/Profile/Views/ProfileView.swift
import SwiftUI

struct ProfileView: View {
    @Environment(\.userService) private var userService
    @State private var viewModel: ProfileViewModel?

    let userId: UUID

    var body: some View {
        Group {
            if let viewModel {
                ProfileContentView(viewModel: viewModel)
            } else {
                ProgressView()
            }
        }
        .task {
            viewModel = ProfileViewModel(userService: userService)
            await viewModel?.loadProfile(userId: userId)
        }
    }
}
```

**Key aspects:**

- Environment values flow down automatically through view hierarchy
- Child views access dependencies without explicit passing
- Easy to override at any point in the hierarchy for testing or customization

## Dependency Container

For complex apps with many interdependent services, use an observable container.

```swift
// Core/Dependencies.swift
import Foundation
import SwiftUI

@MainActor
@Observable
final class Dependencies {

    // MARK: - Services

    let networkService: NetworkServiceProtocol
    let authService: AuthServiceProtocol
    let userService: UserServiceProtocol
    let analyticsService: AnalyticsServiceProtocol
    let cacheService: CacheServiceProtocol

    // MARK: - Init

    init(
        networkService: NetworkServiceProtocol,
        authService: AuthServiceProtocol,
        userService: UserServiceProtocol,
        analyticsService: AnalyticsServiceProtocol,
        cacheService: CacheServiceProtocol
    ) {
        self.networkService = networkService
        self.authService = authService
        self.userService = userService
        self.analyticsService = analyticsService
        self.cacheService = cacheService
    }

    // MARK: - Factory: Production

    static let live: Dependencies = {
        let network = NetworkService()
        let cache = CacheService()

        return Dependencies(
            networkService: network,
            authService: AuthService(networkService: network),
            userService: UserService(networkService: network),
            analyticsService: AnalyticsService(apiKey: Config.analyticsKey),
            cacheService: cache
        )
    }()

    // MARK: - ViewModel Factories

    func makeProfileViewModel() -> ProfileViewModel {
        ProfileViewModel(
            userService: userService,
            analyticsService: analyticsService
        )
    }

    func makeSettingsViewModel() -> SettingsViewModel {
        SettingsViewModel(
            userService: userService,
            authService: authService,
            cacheService: cacheService
        )
    }

    func makeHomeViewModel() -> HomeViewModel {
        HomeViewModel(
            userService: userService,
            analyticsService: analyticsService
        )
    }
}
```

### Environment Key for Container

```swift
// Core/Environment/DependenciesKey.swift
import SwiftUI

private struct DependenciesKey: EnvironmentKey {
    static let defaultValue: Dependencies = .live
}

extension EnvironmentValues {
    var dependencies: Dependencies {
        get { self[DependenciesKey.self] }
        set { self[DependenciesKey.self] = newValue }
    }
}
```

### Inject Container at App Root

```swift
// MyApp.swift
import SwiftUI

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.dependencies, .live)
        }
    }
}
```

### Use Container in Views

```swift
// Features/Profile/Views/ProfileView.swift
import SwiftUI

struct ProfileView: View {
    @Environment(\.dependencies) private var dependencies
    @State private var viewModel: ProfileViewModel?

    let userId: UUID

    var body: some View {
        Group {
            if let viewModel {
                ProfileContentView(viewModel: viewModel)
            } else {
                ProgressView()
            }
        }
        .task {
            viewModel = dependencies.makeProfileViewModel()
            await viewModel?.loadProfile(userId: userId)
        }
    }
}
```

**Key aspects:**

- Single source of truth for all dependencies
- Factory methods ensure consistent ViewModel construction
- Easy to swap entire dependency graph for testing

## Preview Configuration

Create preview-specific dependencies with canned data for SwiftUI previews.

```swift
// Core/Services/Preview/PreviewUserService.swift
final class PreviewUserService: UserServiceProtocol {

    func fetchUser(id: UUID) async throws -> User {
        // Simulate network delay
        try await Task.sleep(for: .milliseconds(500))

        return User(
            id: id,
            name: "Preview User",
            email: "preview@example.com",
            avatarURL: URL(string: "https://picsum.photos/200"),
            createdAt: Date()
        )
    }

    func updateUser(_ user: User) async throws -> User {
        try await Task.sleep(for: .milliseconds(300))
        return user
    }

    func deleteUser(id: UUID) async throws {
        try await Task.sleep(for: .milliseconds(200))
    }
}

// Core/Services/Preview/PreviewAnalyticsService.swift
final class PreviewAnalyticsService: AnalyticsServiceProtocol {
    func track(event: String, properties: [String: Any]) {
        print("[Preview Analytics] \(event): \(properties)")
    }

    func identify(userId: String) {
        print("[Preview Analytics] Identified: \(userId)")
    }

    func reset() {
        print("[Preview Analytics] Reset")
    }
}
```

### Preview Dependencies Extension

```swift
// Core/Dependencies+Preview.swift
import Foundation

extension Dependencies {
    @MainActor
    static let preview: Dependencies = {
        let network = PreviewNetworkService()

        return Dependencies(
            networkService: network,
            authService: PreviewAuthService(),
            userService: PreviewUserService(),
            analyticsService: PreviewAnalyticsService(),
            cacheService: PreviewCacheService()
        )
    }()
}
```

### Use in Previews

```swift
// Features/Profile/Views/ProfileView+Preview.swift
import SwiftUI

#Preview("Profile - Loading") {
    ProfileView(userId: UUID())
        .environment(\.dependencies, .preview)
}

#Preview("Profile - With Data") {
    let viewModel = ProfileViewModel(
        userService: PreviewUserService(),
        analyticsService: PreviewAnalyticsService()
    )
    // Pre-populate with data
    return ProfileContentView(viewModel: viewModel)
        .task {
            await viewModel.loadProfile(userId: UUID())
        }
}

#Preview("Profile - Error State") {
    let viewModel = ProfileViewModel(
        userService: FailingUserService(),
        analyticsService: PreviewAnalyticsService()
    )
    return ProfileView(userId: UUID())
        .environment(\.dependencies, Dependencies(
            networkService: PreviewNetworkService(),
            authService: PreviewAuthService(),
            userService: FailingUserService(),
            analyticsService: PreviewAnalyticsService(),
            cacheService: PreviewCacheService()
        ))
}
```

## Testing Configuration

Create mock services that capture method calls and return configurable results.

```swift
// Tests/Mocks/MockUserService.swift
import Foundation
@testable import MyApp

final class MockUserService: UserServiceProtocol {

    // MARK: - Fetch User

    var fetchUserResult: Result<User, Error> = .success(.mock)
    var fetchCallCount = 0
    var lastFetchedId: UUID?

    func fetchUser(id: UUID) async throws -> User {
        fetchCallCount += 1
        lastFetchedId = id
        return try fetchUserResult.get()
    }

    // MARK: - Update User

    var updateUserResult: Result<User, Error> = .success(.mock)
    var updateCallCount = 0
    var lastUpdatedUser: User?

    func updateUser(_ user: User) async throws -> User {
        updateCallCount += 1
        lastUpdatedUser = user
        return try updateUserResult.get()
    }

    // MARK: - Delete User

    var deleteUserError: Error?
    var deleteCallCount = 0
    var lastDeletedId: UUID?

    func deleteUser(id: UUID) async throws {
        deleteCallCount += 1
        lastDeletedId = id
        if let error = deleteUserError {
            throw error
        }
    }
}

// Tests/Mocks/MockAnalyticsService.swift
final class MockAnalyticsService: AnalyticsServiceProtocol {

    var trackedEvents: [(event: String, properties: [String: Any])] = []
    var identifiedUserId: String?
    var resetCallCount = 0

    func track(event: String, properties: [String: Any]) {
        trackedEvents.append((event, properties))
    }

    func identify(userId: String) {
        identifiedUserId = userId
    }

    func reset() {
        resetCallCount += 1
    }
}
```

### XCTest with Mocks

```swift
// Tests/Features/Profile/ProfileViewModelTests.swift
import XCTest
@testable import MyApp

final class ProfileViewModelTests: XCTestCase {

    private var mockUserService: MockUserService!
    private var mockAnalyticsService: MockAnalyticsService!
    private var viewModel: ProfileViewModel!

    @MainActor
    override func setUp() {
        super.setUp()
        mockUserService = MockUserService()
        mockAnalyticsService = MockAnalyticsService()
        viewModel = ProfileViewModel(
            userService: mockUserService,
            analyticsService: mockAnalyticsService
        )
    }

    // MARK: - Load Profile Tests

    @MainActor
    func testLoadProfileCallsServiceWithCorrectId() async {
        let userId = UUID()

        await viewModel.loadProfile(userId: userId)

        XCTAssertEqual(mockUserService.fetchCallCount, 1)
        XCTAssertEqual(mockUserService.lastFetchedId, userId)
    }

    @MainActor
    func testLoadProfileSuccessSetsUser() async {
        let expectedUser = User.mock
        mockUserService.fetchUserResult = .success(expectedUser)

        await viewModel.loadProfile(userId: expectedUser.id)

        XCTAssertEqual(viewModel.user?.id, expectedUser.id)
        XCTAssertEqual(viewModel.user?.name, expectedUser.name)
        XCTAssertNil(viewModel.error)
        XCTAssertFalse(viewModel.isLoading)
    }

    @MainActor
    func testLoadProfileFailureSetsError() async {
        let expectedError = NSError(domain: "test", code: 404)
        mockUserService.fetchUserResult = .failure(expectedError)

        await viewModel.loadProfile(userId: UUID())

        XCTAssertNil(viewModel.user)
        XCTAssertNotNil(viewModel.error)
        XCTAssertFalse(viewModel.isLoading)
    }

    @MainActor
    func testLoadProfileTracksAnalytics() async {
        await viewModel.loadProfile(userId: UUID())

        XCTAssertEqual(mockAnalyticsService.trackedEvents.count, 2)
        XCTAssertEqual(mockAnalyticsService.trackedEvents[0].event, "profile_load_started")
        XCTAssertEqual(mockAnalyticsService.trackedEvents[1].event, "profile_load_success")
    }

    // MARK: - Update Profile Tests

    @MainActor
    func testUpdateProfileUpdatesUser() async {
        // Load initial user
        mockUserService.fetchUserResult = .success(.mock)
        await viewModel.loadProfile(userId: UUID())

        // Configure update result
        var updatedUser = User.mock
        updatedUser.name = "New Name"
        updatedUser.email = "new@example.com"
        mockUserService.updateUserResult = .success(updatedUser)

        // Perform update
        await viewModel.updateProfile(name: "New Name", email: "new@example.com")

        XCTAssertEqual(viewModel.user?.name, "New Name")
        XCTAssertEqual(viewModel.user?.email, "new@example.com")
        XCTAssertEqual(mockUserService.updateCallCount, 1)
    }

    @MainActor
    func testUpdateProfileWithoutUserDoesNothing() async {
        await viewModel.updateProfile(name: "New Name", email: "new@example.com")

        XCTAssertEqual(mockUserService.updateCallCount, 0)
    }
}

// MARK: - Test Helpers

extension User {
    static var mock: User {
        User(
            id: UUID(),
            name: "Test User",
            email: "test@example.com",
            avatarURL: nil,
            createdAt: Date()
        )
    }
}
```

## Lazy Initialization

Defer expensive initialization until first use for better app startup performance.

### Using Computed Property with Backing Storage

```swift
// Core/Services/DatabaseService.swift
final class DatabaseService {
    private let configuration: DatabaseConfiguration

    init(configuration: DatabaseConfiguration) {
        self.configuration = configuration
        // Expensive setup: opening connections, migrations, etc.
        setupDatabase()
    }

    private func setupDatabase() {
        // Heavy initialization work
    }

    func query(_ sql: String) async throws -> [Row] {
        // Execute query
        []
    }
}
```

```swift
// Core/Dependencies.swift - Lazy Pattern with Computed Property
@MainActor
@Observable
final class Dependencies {

    // Eager services - cheap to initialize
    let networkService: NetworkServiceProtocol
    let analyticsService: AnalyticsServiceProtocol

    // Lazy services - expensive to initialize
    private var _databaseService: DatabaseService?
    var databaseService: DatabaseService {
        if _databaseService == nil {
            _databaseService = DatabaseService(configuration: .default)
        }
        return _databaseService!
    }

    private var _imageCache: ImageCacheService?
    var imageCache: ImageCacheService {
        if _imageCache == nil {
            _imageCache = ImageCacheService(maxSize: 100_000_000)
        }
        return _imageCache!
    }

    init(
        networkService: NetworkServiceProtocol,
        analyticsService: AnalyticsServiceProtocol
    ) {
        self.networkService = networkService
        self.analyticsService = analyticsService
    }
}
```

### Using Swift's lazy var

```swift
// Core/Dependencies.swift - Using lazy var
@MainActor
final class Dependencies {

    // Eager services
    let networkService: NetworkServiceProtocol
    let analyticsService: AnalyticsServiceProtocol

    // Lazy services - initialized on first access
    lazy var databaseService: DatabaseService = {
        DatabaseService(configuration: .default)
    }()

    lazy var imageCache: ImageCacheService = {
        ImageCacheService(maxSize: 100_000_000)
    }()

    lazy var searchService: SearchService = {
        SearchService(networkService: networkService)
    }()

    init(
        networkService: NetworkServiceProtocol,
        analyticsService: AnalyticsServiceProtocol
    ) {
        self.networkService = networkService
        self.analyticsService = analyticsService
    }
}
```

**Note:** `lazy var` cannot be used with `@Observable` macro. Use the computed property pattern when the container needs to be observable.

### Lazy with Protocol Type

```swift
// Core/Dependencies.swift - Lazy with protocols
@MainActor
final class Dependencies {

    private let config: AppConfiguration

    // Lazy services that depend on configuration
    private var _databaseService: DatabaseServiceProtocol?
    var databaseService: DatabaseServiceProtocol {
        if _databaseService == nil {
            _databaseService = config.useMockData
                ? MockDatabaseService()
                : DatabaseService(configuration: config.databaseConfig)
        }
        return _databaseService!
    }

    init(config: AppConfiguration) {
        self.config = config
    }
}
```

**Key aspects:**

- Lazy initialization improves app launch time
- Expensive services (database, large caches) initialize only when needed
- Computed property pattern works with `@Observable`
- `lazy var` provides simpler syntax when observability isn't needed

## Benefits

- **Testability** - Dependencies can be substituted with mocks for isolated testing
- **Modularity** - Components don't create their own dependencies, reducing coupling
- **Flexibility** - Different configurations for production, preview, and test environments
- **Maintainability** - Centralized dependency management simplifies updates
- **Performance** - Lazy initialization defers costly setup until actually needed
