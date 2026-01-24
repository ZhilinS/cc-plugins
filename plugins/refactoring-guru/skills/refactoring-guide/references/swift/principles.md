# Swift Style Principles

## Value Types First

Prefer structs over classes. Use classes only when you need identity semantics, inheritance, or reference behavior (like shared mutable state).

```swift
// Bad - using class for simple data
class User {
    var id: String
    var name: String
    var email: String

    init(id: String, name: String, email: String) {
        self.id = id
        self.name = name
        self.email = email
    }
}

// Good - struct for data models
struct User {
    let id: String
    var name: String
    var email: String
}
```

## Protocol-Oriented Design

Define behavior through protocols, not inheritance. Use protocol extensions to provide default implementations.

```swift
// Bad - inheritance hierarchy
class BaseRepository {
    func save(_ item: Any) { }
    func fetch(id: String) -> Any? { nil }
}

class UserRepository: BaseRepository {
    override func save(_ item: Any) { }
    override func fetch(id: String) -> Any? { nil }
}

// Good - protocol with extension defaults
protocol Repository {
    associatedtype Item
    func save(_ item: Item) async throws
    func fetch(id: String) async throws -> Item?
}

extension Repository {
    func saveAll(_ items: [Item]) async throws {
        for item in items {
            try await save(item)
        }
    }
}

struct UserRepository: Repository {
    func save(_ item: User) async throws { }
    func fetch(id: String) async throws -> User? { nil }
}
```

## Explicit Over Implicit

Avoid force unwrapping. Use guard let for early exits. Prefer explicit error handling over silent failures.

```swift
// Bad - force unwrapping and implicit behavior
func processUser(data: [String: Any]) -> User {
    let id = data["id"] as! String
    let name = data["name"] as! String
    return User(id: id, name: name, email: data["email"] as! String)
}

// Good - explicit unwrapping and error handling
func processUser(data: [String: Any]) throws -> User {
    guard let id = data["id"] as? String,
          let name = data["name"] as? String,
          let email = data["email"] as? String else {
        throw ParseError.missingField
    }
    return User(id: id, name: name, email: email)
}
```

## Composition Over Inheritance

Build views from small components. Use ViewModifiers and composition instead of base view classes.

```swift
// Bad - trying to inherit views
class BaseCardView: UIView {
    func setupShadow() { }
    func setupCorners() { }
}

class UserCardView: BaseCardView {
    override func setupShadow() { }
}

// Good - composition with modifiers
struct CardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(Color.white)
            .cornerRadius(12)
            .shadow(radius: 4)
    }
}

struct UserCard: View {
    let user: User

    var body: some View {
        VStack {
            Text(user.name)
            Text(user.email)
        }
        .modifier(CardModifier())
    }
}
```

## Immutability by Default

Use let unless mutation is required. Prefer immutable data models that produce new instances on change.

```swift
// Bad - mutable state everywhere
class Order {
    var items: [Item] = []
    var status: Status = .pending

    func addItem(_ item: Item) {
        items.append(item)
    }

    func complete() {
        status = .completed
    }
}

// Good - immutable with transformations
struct Order {
    let items: [Item]
    let status: Status

    func adding(_ item: Item) -> Order {
        Order(items: items + [item], status: status)
    }

    func completed() -> Order {
        Order(items: items, status: .completed)
    }
}
```

## Fail Fast, Recover Gracefully

Validate at system boundaries. Use typed errors for recoverable failures. Use preconditions and assertions for programmer errors.

```swift
// Bad - silent failures and generic errors
func withdraw(amount: Double) -> Double? {
    if amount <= 0 { return nil }
    if amount > balance { return nil }
    return balance - amount
}

// Good - typed errors and clear failure modes
enum WithdrawalError: Error {
    case invalidAmount
    case insufficientFunds(available: Decimal)
}

func withdraw(amount: Decimal) throws -> Decimal {
    precondition(amount > 0, "Amount must be positive") // Programmer error

    guard amount <= balance else {
        throw WithdrawalError.insufficientFunds(available: balance)
    }

    return balance - amount
}
```
