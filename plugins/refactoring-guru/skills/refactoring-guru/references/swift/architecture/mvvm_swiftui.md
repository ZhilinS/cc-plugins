# MVVM Architecture for SwiftUI

A clean architecture pattern that separates UI from business logic using ViewModels with Swift's `@Observable` macro. Views observe state changes automatically, enabling reactive and testable code.

## Directory Structure

```
MyApp/
├── MyApp.swift                          # App entry point
│
├── Core/
│   ├── Models/                          # Domain entities
│   │   ├── User.swift
│   │   ├── Profile.swift
│   │   └── Settings.swift
│   │
│   ├── Services/
│   │   ├── Protocols/                   # Service contracts
│   │   │   ├── UserServiceProtocol.swift
│   │   │   ├── AuthServiceProtocol.swift
│   │   │   └── NetworkServiceProtocol.swift
│   │   │
│   │   ├── UserService.swift            # Concrete implementations
│   │   ├── AuthService.swift
│   │   └── NetworkService.swift
│   │
│   └── Utilities/
│       ├── Extensions/
│       │   ├── Date+Formatting.swift
│       │   └── String+Validation.swift
│       └── Helpers/
│           └── KeychainHelper.swift
│
├── Features/                            # Feature modules
│   ├── Auth/
│   │   ├── Views/
│   │   │   ├── LoginView.swift
│   │   │   └── SignUpView.swift
│   │   └── ViewModels/
│   │       ├── LoginViewModel.swift
│   │       └── SignUpViewModel.swift
│   │
│   ├── Home/
│   │   ├── Views/
│   │   │   ├── HomeView.swift
│   │   │   └── DashboardView.swift
│   │   └── ViewModels/
│   │       └── HomeViewModel.swift
│   │
│   └── Profile/
│       ├── Views/
│       │   ├── ProfileView.swift
│       │   └── EditProfileView.swift
│       └── ViewModels/
│           └── ProfileViewModel.swift
│
├── Shared/
│   ├── Components/                      # Reusable UI components
│   │   ├── LoadingView.swift
│   │   ├── ErrorView.swift
│   │   └── AsyncButton.swift
│   │
│   └── Modifiers/                       # Custom view modifiers
│       ├── CardModifier.swift
│       └── ShakeModifier.swift
│
└── Resources/
    ├── Assets.xcassets
    └── Localizable.strings
```

## Layer Responsibilities

### Models (`Core/Models/`)

Pure data structures with no dependencies on external systems.

```swift
// Core/Models/User.swift
struct User: Identifiable, Codable {
    let id: UUID
    var name: String
    var email: String
    var avatarURL: URL?
    let createdAt: Date
}
```

### Service Protocols (`Core/Services/Protocols/`)

Abstract interfaces that define contracts for external interactions.

```swift
// Core/Services/Protocols/UserServiceProtocol.swift
protocol UserServiceProtocol: Sendable {
    func fetchUser(id: UUID) async throws -> User
    func updateUser(_ user: User) async throws -> User
    func deleteUser(id: UUID) async throws
}
```

### Service Implementations (`Core/Services/`)

Concrete implementations of service protocols.

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

## ViewModel Pattern with @Observable

ViewModels hold state and business logic, exposing observable properties that Views bind to.

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

    // MARK: - Init

    init(userService: UserServiceProtocol) {
        self.userService = userService
    }

    // MARK: - Actions

    func loadProfile(userId: UUID) async {
        isLoading = true
        error = nil

        do {
            user = try await userService.fetchUser(id: userId)
        } catch {
            self.error = error
        }

        isLoading = false
    }

    func updateName(_ newName: String) async {
        guard var currentUser = user else { return }

        currentUser.name = newName
        isLoading = true
        error = nil

        do {
            user = try await userService.updateUser(currentUser)
        } catch {
            self.error = error
        }

        isLoading = false
    }
}
```

**Key aspects:**

- `@MainActor` ensures all state mutations happen on the main thread
- `@Observable` enables automatic SwiftUI view updates when properties change
- `private(set)` exposes read-only state while keeping mutations internal
- Async methods use structured concurrency for clean async/await patterns
- Dependencies are injected through the initializer for testability

## View Binding Pattern

Views observe ViewModel state and trigger actions through ViewModel methods.

```swift
// Features/Profile/Views/ProfileView.swift
import SwiftUI

struct ProfileView: View {
    let userId: UUID
    @State private var viewModel: ProfileViewModel

    init(userId: UUID, userService: UserServiceProtocol) {
        self.userId = userId
        self._viewModel = State(initialValue: ProfileViewModel(userService: userService))
    }

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading...")
            } else if let error = viewModel.error {
                ErrorView(error: error) {
                    Task { await viewModel.loadProfile(userId: userId) }
                }
            } else if let user = viewModel.user {
                ProfileContentView(user: user, viewModel: viewModel)
            }
        }
        .task {
            await viewModel.loadProfile(userId: userId)
        }
    }
}

private struct ProfileContentView: View {
    let user: User
    let viewModel: ProfileViewModel

    var body: some View {
        VStack(spacing: 16) {
            AsyncImage(url: user.avatarURL) { image in
                image.resizable().scaledToFill()
            } placeholder: {
                Image(systemName: "person.circle.fill")
                    .resizable()
            }
            .frame(width: 100, height: 100)
            .clipShape(Circle())

            Text(user.name)
                .font(.title)

            Text(user.email)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}
```

**Key aspects:**

- `@State` wraps the ViewModel to maintain its lifecycle with the View
- `Group` provides a clean pattern for handling multiple states
- Content is extracted into a separate view for clarity

## Lifecycle Management

SwiftUI provides lifecycle modifiers that integrate naturally with async ViewModels.

### .task for Async Initialization

```swift
struct ProfileView: View {
    @State private var viewModel: ProfileViewModel
    let userId: UUID

    var body: some View {
        ContentView(viewModel: viewModel)
            .task {
                // Automatically cancelled when view disappears
                await viewModel.loadProfile(userId: userId)
            }
    }
}
```

The `.task` modifier:
- Runs when the view appears
- Automatically cancels when the view disappears
- Creates a new task if the view reappears

### .task(id:) for Reactive Loading

```swift
struct UserDetailView: View {
    @State private var viewModel: UserDetailViewModel
    let userId: UUID

    var body: some View {
        ContentView(viewModel: viewModel)
            .task(id: userId) {
                // Re-runs when userId changes
                await viewModel.loadUser(userId: userId)
            }
    }
}
```

### .refreshable for Pull-to-Refresh

```swift
struct ProfileView: View {
    @State private var viewModel: ProfileViewModel
    let userId: UUID

    var body: some View {
        ScrollView {
            ProfileContentView(viewModel: viewModel)
        }
        .refreshable {
            await viewModel.loadProfile(userId: userId)
        }
        .task {
            await viewModel.loadProfile(userId: userId)
        }
    }
}
```

## State Enum for Complex Screens

For screens with multiple distinct states, use an enum to make state transitions explicit.

```swift
// Features/Data/ViewModels/DataViewModel.swift
import Foundation

@MainActor
@Observable
final class DataViewModel {

    // MARK: - State

    enum State {
        case idle
        case loading
        case loaded([Item])
        case empty
        case error(Error)
    }

    private(set) var state: State = .idle

    // MARK: - Dependencies

    private let dataService: DataServiceProtocol

    // MARK: - Init

    init(dataService: DataServiceProtocol) {
        self.dataService = dataService
    }

    // MARK: - Actions

    func loadData() async {
        state = .loading

        do {
            let items = try await dataService.fetchItems()
            state = items.isEmpty ? .empty : .loaded(items)
        } catch {
            state = .error(error)
        }
    }

    func refresh() async {
        // Keep showing current data during refresh
        do {
            let items = try await dataService.fetchItems()
            state = items.isEmpty ? .empty : .loaded(items)
        } catch {
            state = .error(error)
        }
    }
}
```

```swift
// Features/Data/Views/DataView.swift
import SwiftUI

struct DataView: View {
    @State private var viewModel: DataViewModel

    init(dataService: DataServiceProtocol) {
        self._viewModel = State(initialValue: DataViewModel(dataService: dataService))
    }

    var body: some View {
        contentView
            .task {
                await viewModel.loadData()
            }
    }

    @ViewBuilder
    private var contentView: some View {
        switch viewModel.state {
        case .idle:
            Color.clear

        case .loading:
            ProgressView("Loading...")

        case .loaded(let items):
            List(items) { item in
                ItemRow(item: item)
            }
            .refreshable {
                await viewModel.refresh()
            }

        case .empty:
            ContentUnavailableView(
                "No Items",
                systemImage: "tray",
                description: Text("Add some items to get started.")
            )

        case .error(let error):
            ContentUnavailableView(
                "Error",
                systemImage: "exclamationmark.triangle",
                description: Text(error.localizedDescription)
            )
        }
    }
}
```

**Benefits of State enum:**

- Impossible states are unrepresentable
- Exhaustive switch ensures all states are handled
- State transitions are explicit and traceable

## Testing ViewModels

ViewModels are easily testable because dependencies are injected.

```swift
// Tests/Features/Profile/ProfileViewModelTests.swift
import XCTest
@testable import MyApp

final class ProfileViewModelTests: XCTestCase {

    // MARK: - Mock Service

    final class MockUserService: UserServiceProtocol {
        var fetchUserResult: Result<User, Error> = .success(User.mock)
        var updateUserResult: Result<User, Error> = .success(User.mock)

        func fetchUser(id: UUID) async throws -> User {
            try fetchUserResult.get()
        }

        func updateUser(_ user: User) async throws -> User {
            try updateUserResult.get()
        }

        func deleteUser(id: UUID) async throws {}
    }

    // MARK: - Tests

    @MainActor
    func testLoadProfileSuccess() async {
        // Given
        let mockService = MockUserService()
        let expectedUser = User.mock
        mockService.fetchUserResult = .success(expectedUser)
        let viewModel = ProfileViewModel(userService: mockService)

        // When
        await viewModel.loadProfile(userId: expectedUser.id)

        // Then
        XCTAssertEqual(viewModel.user?.id, expectedUser.id)
        XCTAssertNil(viewModel.error)
        XCTAssertFalse(viewModel.isLoading)
    }

    @MainActor
    func testLoadProfileFailure() async {
        // Given
        let mockService = MockUserService()
        let expectedError = NSError(domain: "test", code: 1)
        mockService.fetchUserResult = .failure(expectedError)
        let viewModel = ProfileViewModel(userService: mockService)

        // When
        await viewModel.loadProfile(userId: UUID())

        // Then
        XCTAssertNil(viewModel.user)
        XCTAssertNotNil(viewModel.error)
        XCTAssertFalse(viewModel.isLoading)
    }

    @MainActor
    func testUpdateNameSuccess() async {
        // Given
        let mockService = MockUserService()
        var updatedUser = User.mock
        updatedUser.name = "Updated Name"
        mockService.fetchUserResult = .success(User.mock)
        mockService.updateUserResult = .success(updatedUser)
        let viewModel = ProfileViewModel(userService: mockService)

        // Load initial user
        await viewModel.loadProfile(userId: User.mock.id)

        // When
        await viewModel.updateName("Updated Name")

        // Then
        XCTAssertEqual(viewModel.user?.name, "Updated Name")
        XCTAssertNil(viewModel.error)
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

## Dependency Injection Pattern

For larger apps, use a dependency container to manage service instances.

```swift
// Core/Dependencies.swift
import Foundation

@MainActor
final class Dependencies {
    static let shared = Dependencies()

    lazy var networkService: NetworkServiceProtocol = NetworkService()
    lazy var userService: UserServiceProtocol = UserService(networkService: networkService)
    lazy var authService: AuthServiceProtocol = AuthService(networkService: networkService)

    private init() {}
}

// Usage in App
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(Dependencies.shared)
        }
    }
}

// Usage in Views
struct ProfileView: View {
    @Environment(Dependencies.self) private var dependencies
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
            viewModel = ProfileViewModel(userService: dependencies.userService)
            await viewModel?.loadProfile(userId: userId)
        }
    }
}
```

## Benefits

- **Testability** - ViewModels can be tested in isolation with mock services
- **Separation of Concerns** - Views handle UI, ViewModels handle logic
- **Reusability** - ViewModels can be reused across different Views
- **Predictability** - State changes flow in one direction, making debugging easier
- **Maintainability** - Clear structure makes code easy to navigate and modify
