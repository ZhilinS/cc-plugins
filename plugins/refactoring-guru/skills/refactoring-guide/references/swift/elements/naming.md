# Naming Conventions

## No "is" Prefix for Boolean Adjectives

When a boolean reads naturally as an adjective without a prefix, skip the prefix. This diverges from Apple convention but reduces noise in code.

```swift
// Awkward - "is" adds noise to natural adjectives
struct ContentView: View {
    @State private var isLoading = false
    @State private var isVisible = true
    @State private var isEnabled = true
    @State private var isExpanded = false

    var body: some View {
        VStack {
            if isLoading {
                ProgressView()
            }

            if isVisible && isEnabled {
                ExpandableSection(isExpanded: $isExpanded)
            }
        }
    }
}

// Clean - adjectives that read naturally as booleans
struct ContentView: View {
    @State private var loading = false
    @State private var visible = true
    @State private var enabled = true
    @State private var expanded = false

    var body: some View {
        VStack {
            if loading {
                ProgressView()
            }

            if visible && enabled {
                ExpandableSection(expanded: $expanded)
            }
        }
    }
}
```

Keep verb prefixes that form natural questions:

```swift
// Good - verb prefixes that form questions
func hasPermission() -> Bool     // "Does it have permission?"
func shouldRetry() -> Bool       // "Should it retry?"
func canEdit() -> Bool           // "Can it edit?"
func willAppear() -> Bool        // "Will it appear?"

// Good - state adjectives without prefix
var loading: Bool     // Is it loading? Yes, it's loading.
var visible: Bool     // Is it visible? Yes, it's visible.
var enabled: Bool     // Is it enabled? Yes, it's enabled.
var selected: Bool    // Is it selected? Yes, it's selected.
```

## Context Gives Meaning to Generic Names

Function context provides meaning to generic names. Variables like `request`, `items`, or `result` are clear within a focused function but unclear in generic contexts.

```swift
// Bad - generic names in generic context
class DataProcessor {
    func process() async throws {
        let request = buildRequest()  // Request for what?
        let items = fetch(request)    // Items of what type?
        for item in items {
            handle(item)              // Handle how?
        }
    }
}

// Good - context makes generic names meaningful
class UserService {
    func fetchUsers() async throws -> [User] {
        let request = URLRequest(url: usersEndpoint)  // Clear: request for users
        let users = try await session.fetch(request)   // Clear: fetching users
        return users
    }
}

// Good - parameter context clarifies local names
func updateCart(with items: [CartItem]) {
    for item in items {          // Clear: cart item
        inventory.reserve(item)
    }
}

// Good - function name provides context
func parseUserResponse(_ data: Data) throws -> User {
    let json = try JSONSerialization.jsonObject(with: data)  // Clear: user JSON
    let user = try decode(json)                               // Clear: the user
    return user
}
```

## Collection Plurals

Use plural names for collections and singular names for items when iterating. Avoid redundant suffixes like `List`, `Array`, or `Collection`.

```swift
// Bad - redundant suffixes and unclear iteration
class OrderManager {
    var orderList: [Order] = []
    var itemArray: [Item] = []
    var userCollection: Set<User> = []

    func process() {
        for o in orderList {
            for i in o.items {
                print(i.name)
            }
        }
    }
}

// Good - plurals for collections, clear iteration variables
class OrderManager {
    var orders: [Order] = []
    var items: [Item] = []
    var users: Set<User> = []

    func process() {
        for order in orders {
            for item in order.items {
                print(item.name)
            }
        }
    }
}

// Good - dictionary naming
var usersByID: [String: User] = [:]
var pricesByProduct: [Product: Decimal] = [:]
var permissionsByRole: [Role: Set<Permission>] = [:]
```

## Method Naming by Action

Simple getters use noun names directly. Action methods use verb prefixes that describe what the method does.

```swift
// Bad - inconsistent verb usage
class UserRepository {
    func getUser(id: String) -> User? { }      // "get" is redundant for simple access
    func retrieveUsers() async -> [User] { }    // Network fetch, but unclear
    func makeUserDTO(from: User) -> UserDTO { } // Creates or transforms?
}

// Good - nouns for simple access, verbs for actions
class UserRepository {
    // Simple property access - use noun
    var currentUser: User? { storage.user }

    // Network operations - "fetch"
    func fetchUser(id: String) async throws -> User { }
    func fetchUsers() async throws -> [User] { }

    // Creating new instances - "create" or "build"
    func createUser(name: String) -> User { }
    func buildRequest(for user: User) -> URLRequest { }

    // Transforming data - "parse" or "convert"
    func parseResponse(_ data: Data) throws -> User { }
    func convertToDTO(_ user: User) -> UserDTO { }

    // Checking conditions - "validate"
    func validateEmail(_ email: String) throws { }

    // Responding to events - "handle"
    func handleLoginSuccess(_ user: User) { }
}
```

Common verb prefixes and their meanings:

| Prefix | Use For | Example |
|--------|---------|---------|
| fetch | Network/async data retrieval | `fetchUsers()` |
| create | Making new instances | `createOrder(items:)` |
| build | Constructing complex objects | `buildRequest()` |
| parse | Converting raw data to types | `parseJSON(_:)` |
| validate | Checking correctness | `validateInput(_:)` |
| convert | Transforming between types | `convertToDTO(_:)` |
| handle | Responding to events | `handleTap()` |
| update | Modifying existing state | `updateProfile(_:)` |
| delete/remove | Removing items | `deleteUser(id:)` |

## Protocol Naming

Protocols describe capabilities. Use `-able`, `-ing` suffixes or nouns that describe roles. Avoid names that sound like concrete types.

```swift
// Bad - sounds like concrete implementations
protocol UserManager { }       // Should be a class name
protocol NetworkHandler { }    // Sounds like a type, not a capability
protocol DataProcessor { }     // Too vague, sounds concrete

// Good - capability with -able
protocol Fetchable {
    associatedtype Output
    func fetch() async throws -> Output
}

protocol Validatable {
    func validate() throws
}

protocol Identifiable {
    var id: ID { get }
}

// Good - active role with -ing
protocol Loading {
    var loading: Bool { get }
}

protocol Logging {
    func log(_ message: String, level: LogLevel)
}

// Good - role nouns
protocol DataSource {
    associatedtype Item
    var numberOfItems: Int { get }
    func item(at index: Int) -> Item
}

protocol Delegate: AnyObject {
    func didComplete()
}

// Good - combined in practice
protocol UserRepositoryProtocol {
    func fetchUser(id: String) async throws -> User
    func saveUser(_ user: User) async throws
}

class UserRepository: UserRepositoryProtocol, Logging {
    // Implementation
}
```

## Type Alias Names

Type aliases use PascalCase. They clarify intent and reduce verbosity for complex types.

```swift
// Bad - unclear inline types
func fetchUser(id: Int, completion: @escaping (Result<User, Error>) -> Void) { }
func processItems(_ items: [(String, Int, Date)]) { }
var handlers: [String: (Data) -> Void] = [:]

// Good - type aliases clarify intent
typealias UserID = Int
typealias CompletionHandler<T> = (Result<T, Error>) -> Void
typealias JSON = [String: Any]

func fetchUser(id: UserID, completion: @escaping CompletionHandler<User>) { }

// Good - complex tuples get named types
typealias PricePoint = (sku: String, price: Int, timestamp: Date)
func processPricePoints(_ points: [PricePoint]) { }

// Good - closure types
typealias DataHandler = (Data) -> Void
typealias AsyncOperation = () async throws -> Void
var handlers: [String: DataHandler] = [:]
```

## Avoid Abbreviations

Use full words except for universally understood abbreviations. Clarity beats brevity.

```swift
// Bad - unclear abbreviations
func usrInfo(usrId: String) -> UsrDTO? { }
func calcTtl(amt: Int, qty: Int) -> Int { }
let cfg = loadCfg()
let mgr = UserMgr()
let btn = UIButton()
var currIdx = 0

// Good - full words
func userInfo(userId: String) -> UserDTO? { }
func calculateTotal(amount: Int, quantity: Int) -> Int { }
let config = loadConfig()
let manager = UserManager()
let button = UIButton()
var currentIndex = 0

// Good - universally understood abbreviations
var userID: String          // ID is universal
let apiURL: URL             // URL, API are universal
let httpClient: HTTPClient  // HTTP is universal
var maxRetries: Int         // max is universal
let minValue: Int           // min is universal
```

Universal abbreviations that are acceptable:

| Abbreviation | Meaning |
|--------------|---------|
| ID | Identifier |
| URL | Uniform Resource Locator |
| HTTP/HTTPS | Hypertext Transfer Protocol |
| API | Application Programming Interface |
| JSON | JavaScript Object Notation |
| UI | User Interface |
| max/min | Maximum/Minimum |

## Constants

Swift uses camelCase for constants, not SCREAMING_SNAKE_CASE. Group related constants in caseless enums to prevent instantiation.

```swift
// Bad - other language conventions
let DEFAULT_TIMEOUT = 30
let MAX_RETRY_COUNT = 3
let API_BASE_URL = "https://api.example.com"

class NetworkConfig {
    static let TIMEOUT = 30  // Screaming case
}

// Good - Swift camelCase constants
let defaultTimeout: TimeInterval = 30
let maxRetryCount = 3
let apiBaseURL = URL(string: "https://api.example.com")!

// Good - grouped in caseless enum (prevents instantiation)
enum API {
    static let baseURL = URL(string: "https://api.example.com")!
    static let timeout: TimeInterval = 30
    static let maxRetries = 3
}

enum Layout {
    static let defaultPadding: CGFloat = 16
    static let cornerRadius: CGFloat = 8
    static let iconSize: CGFloat = 24
}

// Usage
let request = URLRequest(url: API.baseURL)
request.timeoutInterval = API.timeout

// Good - related constants in context
struct CacheConfig {
    let maxSize: Int
    let expirationInterval: TimeInterval

    static let `default` = CacheConfig(
        maxSize: 100,
        expirationInterval: 3600
    )
}
```
