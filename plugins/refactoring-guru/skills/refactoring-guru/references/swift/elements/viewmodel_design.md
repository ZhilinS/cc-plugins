# ViewModel Design

## One ViewModel Per Screen

Each screen gets its own focused ViewModel. God-object ViewModels with dozens of properties become impossible to reason about and test.

```swift
// Bad - god-object ViewModel handling everything
@Observable
class AppViewModel {
    var currentUser: User?
    var users: [User] = []
    var selectedUser: User?
    var isLoadingUsers = false
    var userSearchText = ""
    var orders: [Order] = []
    var selectedOrder: Order?
    var isLoadingOrders = false
    var orderFilter: OrderFilter = .all
    var cart: [CartItem] = []
    var promoCode = ""
    var isCheckingOut = false
    var settings: Settings = .default
    var notificationsEnabled = true
    var darkModeEnabled = false
    var profile: Profile?
    var isEditingProfile = false
    // ... 30 more properties

    func loadUsers() { }
    func searchUsers() { }
    func loadOrders() { }
    func filterOrders() { }
    func addToCart() { }
    func checkout() { }
    func updateSettings() { }
    // ... 20 more methods
}

// Good - focused ViewModels per feature
@Observable
class UserListViewModel {
    var users: [User] = []
    var isLoading = false
    var searchText = ""

    func loadUsers() async { }
    func search() { }
}

@Observable
class OrderHistoryViewModel {
    var orders: [Order] = []
    var isLoading = false
    var filter: OrderFilter = .all

    var filteredOrders: [Order] {
        filter == .all ? orders : orders.filter { $0.status == filter }
    }

    func loadOrders() async { }
}

@Observable
class CartViewModel {
    var items: [CartItem] = []
    var promoCode = ""

    var total: Decimal {
        items.reduce(0) { $0 + $1.price * Decimal($1.quantity) }
    }

    func addItem(_ item: CartItem) { }
    func checkout() async { }
}
```

## Public Read-Only State

Use `private(set)` for state that views observe but shouldn't modify directly. This prevents accidental state corruption and makes the data flow clear.

```swift
// Bad - all state publicly mutable
@Observable
class ProfileViewModel {
    var user: User?
    var isLoading = false
    var errorMessage: String?

    func loadProfile() async {
        isLoading = true
        // ...
    }
}

// View can accidentally corrupt state
struct ProfileView: View {
    @State private var viewModel = ProfileViewModel()

    var body: some View {
        Button("Oops") {
            viewModel.isLoading = true  // Breaks loading state
            viewModel.user = nil        // Corrupts data
        }
    }
}

// Good - controlled mutations via private(set)
@Observable
class ProfileViewModel {
    private(set) var user: User?
    private(set) var isLoading = false
    private(set) var errorMessage: String?

    func loadProfile() async {
        isLoading = true
        errorMessage = nil

        do {
            user = try await userService.fetchProfile()
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func updateBio(_ bio: String) async {
        guard var currentUser = user else { return }
        currentUser.bio = bio
        user = currentUser
        // Persist change...
    }
}

// View can only trigger actions, not corrupt state
struct ProfileView: View {
    @State private var viewModel = ProfileViewModel()

    var body: some View {
        // viewModel.isLoading = true  // Compile error
        Button("Refresh") {
            Task { await viewModel.loadProfile() }
        }
    }
}
```

## Actions as Methods

Expose actions as methods, not published variables. Methods express intent and can encapsulate validation. Published booleans create unclear, imperative control flow.

```swift
// Bad - using published vars as action triggers
@Observable
class CounterViewModel {
    var count = 0
    var shouldIncrement = false
    var shouldDecrement = false
    var shouldReset = false

    func processActions() {
        if shouldIncrement {
            count += 1
            shouldIncrement = false
        }
        if shouldDecrement {
            count -= 1
            shouldDecrement = false
        }
        if shouldReset {
            count = 0
            shouldReset = false
        }
    }
}

struct CounterView: View {
    @State private var viewModel = CounterViewModel()

    var body: some View {
        VStack {
            Text("\(viewModel.count)")
            Button("+") {
                viewModel.shouldIncrement = true
                viewModel.processActions()  // Easy to forget
            }
        }
    }
}

// Good - methods express intent directly
@Observable
class CounterViewModel {
    private(set) var count = 0

    func increment() {
        count += 1
    }

    func decrement() {
        guard count > 0 else { return }
        count -= 1
    }

    func reset() {
        count = 0
    }
}

struct CounterView: View {
    @State private var viewModel = CounterViewModel()

    var body: some View {
        VStack {
            Text("\(viewModel.count)")
            HStack {
                Button("-") { viewModel.decrement() }
                Button("+") { viewModel.increment() }
                Button("Reset") { viewModel.reset() }
            }
        }
    }
}
```

## Lifecycle with .task Modifier

Use SwiftUI's `.task` modifier for async initialization. It automatically cancels when the view disappears, eliminating manual lifecycle management.

```swift
// Bad - manual Task management with onAppear/onDisappear
struct UserListView: View {
    @State private var viewModel = UserListViewModel()
    @State private var loadTask: Task<Void, Never>?

    var body: some View {
        List(viewModel.users) { user in
            UserRow(user: user)
        }
        .onAppear {
            loadTask = Task {
                await viewModel.loadUsers()
            }
        }
        .onDisappear {
            loadTask?.cancel()
            loadTask = nil
        }
    }
}

// Good - .task handles lifecycle automatically
struct UserListView: View {
    @State private var viewModel = UserListViewModel()

    var body: some View {
        List(viewModel.users) { user in
            UserRow(user: user)
        }
        .task {
            await viewModel.loadUsers()
        }
    }
}

// .task with id: re-runs when the id changes
struct UserDetailView: View {
    let userId: String
    @State private var viewModel = UserDetailViewModel()

    var body: some View {
        UserContent(user: viewModel.user)
            .task(id: userId) {
                await viewModel.loadUser(id: userId)
            }
    }
}
```

## State Enum for Complex States

Use an enum when a screen has multiple mutually exclusive states. Multiple booleans create impossible states and complex conditionals.

```swift
// Bad - multiple booleans create impossible states
@Observable
class ArticleViewModel {
    var article: Article?
    var isLoading = false
    var isEmpty = false
    var error: Error?

    // What if isLoading && error != nil?
    // What if isEmpty && article != nil?
    // 2^4 = 16 possible combinations, most invalid
}

struct ArticleView: View {
    @State private var viewModel = ArticleViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView()
            } else if let error = viewModel.error {
                ErrorView(error: error)
            } else if viewModel.isEmpty {
                EmptyStateView()
            } else if let article = viewModel.article {
                ArticleContent(article: article)
            } else {
                // What state is this?
                EmptyView()
            }
        }
    }
}

// Good - enum makes states explicit and exhaustive
enum ViewState<T> {
    case idle
    case loading
    case loaded(T)
    case empty
    case error(Error)
}

@Observable
class ArticleViewModel {
    private(set) var state: ViewState<Article> = .idle

    func loadArticle(id: String) async {
        state = .loading

        do {
            let article = try await articleService.fetch(id: id)
            state = .loaded(article)
        } catch is ArticleNotFoundError {
            state = .empty
        } catch {
            state = .error(error)
        }
    }
}

struct ArticleView: View {
    let articleId: String
    @State private var viewModel = ArticleViewModel()

    var body: some View {
        Group {
            switch viewModel.state {
            case .idle:
                Color.clear
            case .loading:
                ProgressView()
            case .loaded(let article):
                ArticleContent(article: article)
            case .empty:
                EmptyStateView(message: "Article not found")
            case .error(let error):
                ErrorView(error: error, retry: {
                    Task { await viewModel.loadArticle(id: articleId) }
                })
            }
        }
        .task {
            await viewModel.loadArticle(id: articleId)
        }
    }
}
```

## Dependency Injection via Initializer

Inject dependencies through the initializer for testability. Hardcoded dependencies make testing difficult and couple the ViewModel to concrete implementations.

```swift
// Bad - hardcoded dependency
@Observable
class UserListViewModel {
    private let service = UserService()  // Untestable
    private(set) var users: [User] = []

    func loadUsers() async {
        users = try? await service.fetchUsers() ?? []
    }
}

// Tests require real network calls or swizzling

// Good - injected dependency with protocol
protocol UserServiceProtocol {
    func fetchUsers() async throws -> [User]
}

class UserService: UserServiceProtocol {
    func fetchUsers() async throws -> [User] {
        // Real implementation
    }
}

@Observable
class UserListViewModel {
    private let service: UserServiceProtocol
    private(set) var users: [User] = []

    init(service: UserServiceProtocol = UserService()) {
        self.service = service
    }

    func loadUsers() async {
        users = (try? await service.fetchUsers()) ?? []
    }
}

// Easy to test with mock
class MockUserService: UserServiceProtocol {
    var usersToReturn: [User] = []

    func fetchUsers() async throws -> [User] {
        usersToReturn
    }
}

func testLoadUsers() async {
    let mock = MockUserService()
    mock.usersToReturn = [User(name: "Test")]
    let viewModel = UserListViewModel(service: mock)

    await viewModel.loadUsers()

    XCTAssertEqual(viewModel.users.count, 1)
    XCTAssertEqual(viewModel.users.first?.name, "Test")
}

// Production view uses default
struct UserListView: View {
    @State private var viewModel = UserListViewModel()
    // ...
}

// Preview uses mock
#Preview {
    let mock = MockUserService()
    mock.usersToReturn = User.previews
    return UserListView(viewModel: UserListViewModel(service: mock))
}
```
