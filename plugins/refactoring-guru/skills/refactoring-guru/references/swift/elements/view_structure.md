# View Structure

## Keep Views Under 50 Lines

Extract subviews when a view grows beyond 50 lines. Large views become hard to reason about and hide the overall structure.

```swift
// Bad - monolithic view with everything inline
struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Header section - 15 lines
                ZStack(alignment: .bottomTrailing) {
                    AsyncImage(url: viewModel.user.avatarURL) { image in
                        image.resizable().aspectRatio(contentMode: .fill)
                    } placeholder: {
                        Color.gray
                    }
                    .frame(width: 120, height: 120)
                    .clipShape(Circle())

                    Button(action: { viewModel.editAvatar() }) {
                        Image(systemName: "camera.fill")
                            .padding(8)
                            .background(Color.blue)
                            .clipShape(Circle())
                    }
                }

                Text(viewModel.user.name)
                    .font(.title)
                Text(viewModel.user.bio)
                    .foregroundColor(.secondary)

                // Stats section - 20 lines
                HStack(spacing: 32) {
                    VStack {
                        Text("\(viewModel.user.posts)")
                            .font(.headline)
                        Text("Posts")
                            .foregroundColor(.secondary)
                    }
                    VStack {
                        Text("\(viewModel.user.followers)")
                            .font(.headline)
                        Text("Followers")
                            .foregroundColor(.secondary)
                    }
                    VStack {
                        Text("\(viewModel.user.following)")
                            .font(.headline)
                        Text("Following")
                            .foregroundColor(.secondary)
                    }
                }

                // Actions section - 15 more lines...
                // Settings section - 20 more lines...
            }
        }
    }
}

// Good - composed from focused subviews
struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                ProfileHeader(user: viewModel.user, onEditAvatar: viewModel.editAvatar)
                ProfileStats(user: viewModel.user)
                ProfileActions(viewModel: viewModel)
                ProfileSettings(viewModel: viewModel)
            }
        }
    }
}

struct ProfileHeader: View {
    let user: User
    let onEditAvatar: () -> Void

    var body: some View {
        VStack {
            AvatarView(url: user.avatarURL, onEdit: onEditAvatar)
            Text(user.name).font(.title)
            Text(user.bio).foregroundColor(.secondary)
        }
    }
}

struct ProfileStats: View {
    let user: User

    var body: some View {
        HStack(spacing: 32) {
            StatItem(value: user.posts, label: "Posts")
            StatItem(value: user.followers, label: "Followers")
            StatItem(value: user.following, label: "Following")
        }
    }
}
```

## Computed Properties for Conditional Content

Use computed properties to break complex conditional logic out of body. The `@ViewBuilder` attribute lets computed properties return different view types.

```swift
// Bad - complex conditionals inline in body
struct OrderStatusView: View {
    let order: Order

    var body: some View {
        VStack {
            if order.status == .pending {
                HStack {
                    Image(systemName: "clock")
                    Text("Waiting for confirmation")
                }
                .foregroundColor(.orange)
                Button("Cancel Order") { }
            } else if order.status == .processing {
                HStack {
                    ProgressView()
                    Text("Processing your order")
                }
                Button("Track Order") { }
            } else if order.status == .shipped {
                HStack {
                    Image(systemName: "shippingbox")
                    Text("On the way!")
                }
                .foregroundColor(.blue)
                Button("Track Package") { }
            } else if order.status == .delivered {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                    Text("Delivered")
                }
                .foregroundColor(.green)
                Button("Leave Review") { }
            }
        }
    }
}

// Good - computed properties isolate conditional logic
struct OrderStatusView: View {
    let order: Order

    var body: some View {
        VStack {
            statusIndicator
            actionButton
        }
    }

    @ViewBuilder
    private var statusIndicator: some View {
        switch order.status {
        case .pending:
            Label("Waiting for confirmation", systemImage: "clock")
                .foregroundColor(.orange)
        case .processing:
            HStack {
                ProgressView()
                Text("Processing your order")
            }
        case .shipped:
            Label("On the way!", systemImage: "shippingbox")
                .foregroundColor(.blue)
        case .delivered:
            Label("Delivered", systemImage: "checkmark.circle.fill")
                .foregroundColor(.green)
        }
    }

    @ViewBuilder
    private var actionButton: some View {
        switch order.status {
        case .pending:
            Button("Cancel Order") { }
        case .processing, .shipped:
            Button("Track Order") { }
        case .delivered:
            Button("Leave Review") { }
        }
    }
}
```

## ViewBuilder for Reusable Layouts

Use `@ViewBuilder` functions for layouts that accept content. This eliminates duplicated styling code across similar UI patterns.

```swift
// Bad - duplicated layout code everywhere
struct SettingsView: View {
    var body: some View {
        VStack(spacing: 16) {
            // Card 1
            VStack(alignment: .leading, spacing: 8) {
                Text("Account")
                    .font(.headline)
                Divider()
                Text("Edit your profile and preferences")
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(radius: 2)

            // Card 2 - same wrapper, different content
            VStack(alignment: .leading, spacing: 8) {
                Text("Notifications")
                    .font(.headline)
                Divider()
                Toggle("Push notifications", isOn: .constant(true))
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(radius: 2)

            // Card 3 - same wrapper again
            VStack(alignment: .leading, spacing: 8) {
                Text("Privacy")
                    .font(.headline)
                Divider()
                Text("Manage your data")
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(radius: 2)
        }
    }
}

// Good - generic Card extracts the pattern
struct Card<Content: View>: View {
    let title: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
            Divider()
            content()
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct SettingsView: View {
    var body: some View {
        VStack(spacing: 16) {
            Card(title: "Account") {
                Text("Edit your profile and preferences")
                    .foregroundColor(.secondary)
            }

            Card(title: "Notifications") {
                Toggle("Push notifications", isOn: .constant(true))
            }

            Card(title: "Privacy") {
                Text("Manage your data")
                    .foregroundColor(.secondary)
            }
        }
    }
}
```

## Avoid Logic in View Body

Views should only describe UI. Delegate calculations, formatting, and business logic to the ViewModel. This keeps views testable and focused.

```swift
// Bad - business logic mixed into view
struct CartView: View {
    @State private var items: [CartItem] = []
    @State private var promoCode: String = ""

    var body: some View {
        VStack {
            ForEach(items) { item in
                HStack {
                    Text(item.name)
                    Spacer()
                    // Calculation in view
                    Text("$\(String(format: "%.2f", Double(item.price) * Double(item.quantity) / 100.0))")
                }
            }

            Divider()

            // Complex logic in view
            let subtotal = items.reduce(0) { $0 + $1.price * $1.quantity }
            let discount = promoCode == "SAVE20" ? Double(subtotal) * 0.2 : 0
            let tax = Double(subtotal - Int(discount)) * 0.08
            let total = Double(subtotal) - discount + tax

            Text("Subtotal: $\(String(format: "%.2f", Double(subtotal) / 100.0))")
            if discount > 0 {
                Text("Discount: -$\(String(format: "%.2f", discount / 100.0))")
                    .foregroundColor(.green)
            }
            Text("Tax: $\(String(format: "%.2f", tax / 100.0))")
            Text("Total: $\(String(format: "%.2f", total / 100.0))")
                .font(.headline)
        }
    }
}

// Good - logic lives in ViewModel, view only describes UI
@Observable
class CartViewModel {
    var items: [CartItem] = []
    var promoCode: String = ""

    var subtotal: Decimal {
        items.reduce(0) { $0 + $1.price * Decimal($1.quantity) }
    }

    var discount: Decimal {
        promoCode == "SAVE20" ? subtotal * 0.2 : 0
    }

    var tax: Decimal {
        (subtotal - discount) * 0.08
    }

    var total: Decimal {
        subtotal - discount + tax
    }

    func formattedPrice(_ amount: Decimal) -> String {
        amount.formatted(.currency(code: "USD"))
    }
}

struct CartView: View {
    @State private var viewModel = CartViewModel()

    var body: some View {
        VStack {
            ForEach(viewModel.items) { item in
                CartItemRow(item: item, formatPrice: viewModel.formattedPrice)
            }

            Divider()

            PriceSummary(viewModel: viewModel)
        }
    }
}

struct PriceSummary: View {
    let viewModel: CartViewModel

    var body: some View {
        VStack(alignment: .trailing) {
            Text("Subtotal: \(viewModel.formattedPrice(viewModel.subtotal))")

            if viewModel.discount > 0 {
                Text("Discount: -\(viewModel.formattedPrice(viewModel.discount))")
                    .foregroundColor(.green)
            }

            Text("Tax: \(viewModel.formattedPrice(viewModel.tax))")
            Text("Total: \(viewModel.formattedPrice(viewModel.total))")
                .font(.headline)
        }
    }
}
```

## Extract Repeated Subviews

When the same pattern appears multiple times, extract it into a reusable component. This reduces duplication and creates a vocabulary of UI building blocks.

```swift
// Bad - repeated HStack pattern throughout the view
struct UserProfileView: View {
    let user: User

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "envelope")
                    .foregroundColor(.secondary)
                    .frame(width: 24)
                Text("Email")
                    .foregroundColor(.secondary)
                Spacer()
                Text(user.email)
            }

            HStack {
                Image(systemName: "phone")
                    .foregroundColor(.secondary)
                    .frame(width: 24)
                Text("Phone")
                    .foregroundColor(.secondary)
                Spacer()
                Text(user.phone)
            }

            HStack {
                Image(systemName: "mappin")
                    .foregroundColor(.secondary)
                    .frame(width: 24)
                Text("Location")
                    .foregroundColor(.secondary)
                Spacer()
                Text(user.location)
            }

            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(.secondary)
                    .frame(width: 24)
                Text("Joined")
                    .foregroundColor(.secondary)
                Spacer()
                Text(user.joinDate.formatted(date: .abbreviated, time: .omitted))
            }
        }
    }
}

// Good - extracted InfoRow component
struct InfoRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.secondary)
                .frame(width: 24)
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
        }
    }
}

struct UserProfileView: View {
    let user: User

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            InfoRow(icon: "envelope", label: "Email", value: user.email)
            InfoRow(icon: "phone", label: "Phone", value: user.phone)
            InfoRow(icon: "mappin", label: "Location", value: user.location)
            InfoRow(icon: "calendar", label: "Joined",
                    value: user.joinDate.formatted(date: .abbreviated, time: .omitted))
        }
    }
}
```
