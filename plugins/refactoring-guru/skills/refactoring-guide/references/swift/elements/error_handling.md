# Error Handling

## Typed Error Enums

Define domain-specific error types conforming to Error. Typed errors make error handling exhaustive and self-documenting.

```swift
// Bad - generic NSError loses context
func fetchUser(id: Int) throws -> User {
    guard id > 0 else {
        throw NSError(domain: "UserError", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "Invalid user ID"
        ])
    }

    guard let user = database.find(id) else {
        throw NSError(domain: "UserError", code: 2, userInfo: [
            NSLocalizedDescriptionKey: "User not found"
        ])
    }

    return user
}

// Caller can't pattern match on error types
do {
    let user = try fetchUser(id: userId)
} catch {
    // What kind of error? Check code? Check message?
    print(error.localizedDescription)
}

// Good - typed enum with associated values
enum UserError: Error {
    case invalidId(Int)
    case notFound(Int)
    case networkFailure(underlying: Error)
}

func fetchUser(id: Int) throws -> User {
    guard id > 0 else {
        throw UserError.invalidId(id)
    }

    guard let user = database.find(id) else {
        throw UserError.notFound(id)
    }

    return user
}

// Caller can pattern match exhaustively
do {
    let user = try fetchUser(id: userId)
} catch UserError.invalidId(let id) {
    showError("Invalid user ID: \(id)")
} catch UserError.notFound(let id) {
    showError("User \(id) not found")
} catch UserError.networkFailure(let underlying) {
    showError("Network error: \(underlying.localizedDescription)")
}
```

## LocalizedError for User-Facing Messages

Conform to LocalizedError when errors need display text. This separates error identity from presentation and supports localization.

```swift
// Bad - embedding user strings in throw sites
func validateEmail(_ email: String) throws {
    guard email.contains("@") else {
        throw NSError(domain: "Validation", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "Please enter a valid email address",
            NSLocalizedRecoverySuggestionErrorKey: "Email must contain @ symbol"
        ])
    }
}

// Error messages scattered across codebase, hard to localize

// Good - LocalizedError conformance centralizes user-facing text
enum ValidationError: LocalizedError {
    case invalidEmail(String)
    case passwordTooShort(Int)
    case usernameTaken(String)

    var errorDescription: String? {
        switch self {
        case .invalidEmail:
            return String(localized: "Invalid email address")
        case .passwordTooShort(let minimum):
            return String(localized: "Password must be at least \(minimum) characters")
        case .usernameTaken(let name):
            return String(localized: "Username '\(name)' is already taken")
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .invalidEmail:
            return String(localized: "Please enter an email in the format name@example.com")
        case .passwordTooShort:
            return String(localized: "Try adding numbers or special characters")
        case .usernameTaken:
            return String(localized: "Try adding numbers or underscores to make it unique")
        }
    }
}

func validateEmail(_ email: String) throws {
    guard email.contains("@") else {
        throw ValidationError.invalidEmail(email)
    }
}

// View displays error naturally
if let error = viewModel.error {
    Text(error.localizedDescription)
    if let suggestion = (error as? LocalizedError)?.recoverySuggestion {
        Text(suggestion).foregroundStyle(.secondary)
    }
}
```

## Result Type for Async Boundaries

Use Result at API boundaries when you need to capture success/failure without throwing. Result is useful in callbacks and when storing outcomes.

```swift
// Bad - throwing in completion handlers requires awkward patterns
class UserService {
    func fetchUser(id: Int, completion: @escaping (User?, Error?) -> Void) {
        URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(nil, error)
                return
            }

            guard let data = data else {
                completion(nil, NetworkError.noData)
                return
            }

            do {
                let user = try JSONDecoder().decode(User.self, from: data)
                completion(user, nil)
            } catch {
                completion(nil, error)
            }
        }.resume()
    }
}

// Caller deals with optional tuple mess
service.fetchUser(id: 1) { user, error in
    if let user = user {
        // success
    } else if let error = error {
        // failure
    } else {
        // impossible state?
    }
}

// Good - Result captures outcome cleanly
class UserService {
    func fetchUser(id: Int, completion: @escaping (Result<User, Error>) -> Void) {
        URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NetworkError.noData))
                return
            }

            completion(Result { try JSONDecoder().decode(User.self, from: data) })
        }.resume()
    }
}

// Caller handles exactly two cases
service.fetchUser(id: 1) { result in
    switch result {
    case .success(let user):
        self.user = user
    case .failure(let error):
        self.error = error
    }
}

// Good - Result in ViewModel state for UI binding
@Observable
class ProfileViewModel {
    private(set) var result: Result<User, Error>?

    func loadProfile() async {
        result = await Result { try await userService.fetchProfile() }
    }
}

struct ProfileView: View {
    @State private var viewModel = ProfileViewModel()

    var body: some View {
        Group {
            switch viewModel.result {
            case .none:
                ProgressView()
            case .success(let user):
                ProfileContent(user: user)
            case .failure(let error):
                ErrorView(error: error)
            }
        }
        .task { await viewModel.loadProfile() }
    }
}
```

## When to Throw vs Return Optional

Throw for unexpected failures. Return optional for expected "not found" cases. The distinction affects caller control flow.

```swift
// Bad - throwing for expected "not found" case
func findUser(byEmail email: String) throws -> User {
    guard let user = database.users.first(where: { $0.email == email }) else {
        throw UserError.notFound  // Is "not found" really an error?
    }
    return user
}

// Caller forced into do-catch for normal control flow
do {
    let user = try findUser(byEmail: email)
    showProfile(user)
} catch {
    showRegistrationPrompt()  // Not an error, just not found
}

// Bad - returning optional for unexpected failures
func fetchUser(id: Int) -> User? {
    guard id > 0 else { return nil }  // Was this invalid input or network failure?

    do {
        return try networkClient.fetch(User.self, endpoint: "/users/\(id)")
    } catch {
        return nil  // Swallows network errors
    }
}

// Caller can't distinguish "doesn't exist" from "network down"
if let user = fetchUser(id: userId) {
    showProfile(user)
} else {
    // Should we show "user not found" or "please check your connection"?
}

// Good - optional for expected "not found"
func findUser(byEmail email: String) -> User? {
    database.users.first { $0.email == email }
}

// Caller uses natural optional handling
if let existingUser = findUser(byEmail: email) {
    showProfile(existingUser)
} else {
    showRegistrationPrompt()
}

// Good - throw for unexpected failures
func fetchUser(id: Int) throws -> User {
    guard id > 0 else {
        throw UserError.invalidId(id)
    }

    return try networkClient.fetch(User.self, endpoint: "/users/\(id)")
}

// Caller can handle different failure modes
do {
    let user = try fetchUser(id: userId)
    showProfile(user)
} catch UserError.invalidId {
    showError("Invalid user ID")
} catch is NetworkError {
    showError("Please check your connection")
}
```

## Guard for Early Exit

Use guard to validate preconditions and exit early. This keeps the happy path at the lowest indentation level.

```swift
// Bad - nested conditionals pyramid
func processOrder(userId: String?, items: [Item]?, paymentMethod: PaymentMethod?) -> Order? {
    if let userId = userId {
        if let items = items {
            if !items.isEmpty {
                if let paymentMethod = paymentMethod {
                    if paymentMethod.isValid {
                        let order = Order(
                            userId: userId,
                            items: items,
                            payment: paymentMethod
                        )
                        return order
                    } else {
                        print("Invalid payment")
                        return nil
                    }
                } else {
                    print("No payment method")
                    return nil
                }
            } else {
                print("Empty cart")
                return nil
            }
        } else {
            print("No items")
            return nil
        }
    } else {
        print("No user")
        return nil
    }
}

// Good - guard statements for flat control flow
func processOrder(userId: String?, items: [Item]?, paymentMethod: PaymentMethod?) -> Order? {
    guard let userId = userId else {
        print("No user")
        return nil
    }

    guard let items = items, !items.isEmpty else {
        print("Cart is empty")
        return nil
    }

    guard let paymentMethod = paymentMethod, paymentMethod.isValid else {
        print("Invalid payment method")
        return nil
    }

    return Order(userId: userId, items: items, payment: paymentMethod)
}

// Good - throwing version with guard
func processOrder(userId: String?, items: [Item]?, paymentMethod: PaymentMethod?) throws -> Order {
    guard let userId = userId else {
        throw OrderError.missingUser
    }

    guard let items = items, !items.isEmpty else {
        throw OrderError.emptyCart
    }

    guard let paymentMethod = paymentMethod else {
        throw OrderError.missingPayment
    }

    guard paymentMethod.isValid else {
        throw OrderError.invalidPayment(paymentMethod)
    }

    return Order(userId: userId, items: items, payment: paymentMethod)
}
```

## Do-Catch Specificity

Catch specific errors before generic ones. This enables precise error handling and prevents swallowing unexpected errors.

```swift
// Bad - generic catch swallows all errors
func purchaseItem(itemId: String) async {
    do {
        let item = try await inventory.reserve(itemId: itemId)
        try await payment.charge(amount: item.price)
        try await fulfillment.ship(item: item)
    } catch {
        // What failed? Inventory? Payment? Shipping?
        showError("Purchase failed")
    }
}

// Bad - catches errors in wrong order
func purchaseItem(itemId: String) async {
    do {
        try await payment.charge(amount: amount)
    } catch {
        // Generic catch first - specific catches never run
        showError("Something went wrong")
    } catch PaymentError.insufficientFunds {
        showError("Not enough funds")
    } catch PaymentError.cardDeclined {
        showError("Card was declined")
    }
}

// Good - specific catches with appropriate responses
enum PaymentError: Error {
    case insufficientFunds(shortfall: Decimal)
    case cardDeclined(reason: String)
    case cardExpired
    case networkUnavailable
}

func purchaseItem(itemId: String) async {
    do {
        let item = try await inventory.reserve(itemId: itemId)
        try await payment.charge(amount: item.price)
        try await fulfillment.ship(item: item)
        showConfirmation(item: item)
    } catch PaymentError.insufficientFunds(let shortfall) {
        showError("You need \(shortfall.formatted(.currency(code: "USD"))) more")
    } catch PaymentError.cardDeclined(let reason) {
        showError("Card declined: \(reason)")
    } catch PaymentError.cardExpired {
        showError("Your card has expired")
        promptForNewCard()
    } catch PaymentError.networkUnavailable {
        showError("Please check your connection and try again")
    } catch is InventoryError {
        showError("Item is no longer available")
    } catch {
        // Truly unexpected error - log and show generic message
        logger.error("Unexpected purchase error: \(error)")
        showError("Purchase failed. Please try again.")
    }
}

// Good - using pattern matching for related errors
func handleAuthError(_ error: Error) {
    switch error {
    case AuthError.invalidCredentials:
        showError("Invalid email or password")
    case AuthError.accountLocked(let until):
        showError("Account locked until \(until.formatted())")
    case AuthError.sessionExpired:
        promptForReauthentication()
    case let networkError as NetworkError where networkError.isRetryable:
        scheduleRetry()
    case is NetworkError:
        showError("Connection problem")
    default:
        showError("Authentication failed")
    }
}
```
