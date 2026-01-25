# SwiftUI Navigation Patterns

Modern SwiftUI navigation using NavigationStack, deep linking, and the Coordinator pattern.

## NavigationStack with Path

Type-safe navigation using an enum-based routing system.

### Bad

```swift
// String-based navigation with no type safety
struct ContentView: View {
    @State private var selectedScreen: String?

    var body: some View {
        NavigationView {  // Deprecated
            List {
                NavigationLink("User", tag: "user", selection: $selectedScreen) {
                    UserView()
                }
                NavigationLink("Settings", tag: "settings", selection: $selectedScreen) {
                    SettingsView()
                }
            }
        }
    }
}

// Passing data through initializers deeply nested
struct UserView: View {
    var body: some View {
        NavigationLink("Order History") {
            OrderHistoryView(userId: 123)  // Hard to manage back stack
        }
    }
}
```

### Good

```swift
// Type-safe routes with associated values
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
                        UserDetailView(userId: userId, path: $path)
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

struct HomeView: View {
    @Binding var path: NavigationPath

    var body: some View {
        List {
            Button("View Profile") {
                path.append(Route.userDetail(userId: 42))
            }

            Button("Settings") {
                path.append(Route.settings)
            }

            Button("Order History") {
                path.append(Route.orderHistory)
            }
        }
        .navigationTitle("Home")
    }
}

struct UserDetailView: View {
    let userId: Int
    @Binding var path: NavigationPath

    var body: some View {
        VStack {
            Text("User \(userId)")

            Button("View Orders") {
                path.append(Route.orderHistory)
            }
        }
        .navigationTitle("Profile")
    }
}

struct OrderHistoryView: View {
    @Binding var path: NavigationPath
    let orders = ["ORD-001", "ORD-002", "ORD-003"]

    var body: some View {
        List(orders, id: \.self) { orderId in
            Button(orderId) {
                path.append(Route.orderDetail(orderId: orderId))
            }
        }
        .navigationTitle("Orders")
    }
}

struct OrderDetailView: View {
    let orderId: String

    var body: some View {
        Text("Order: \(orderId)")
            .navigationTitle("Order Detail")
    }
}

struct SettingsView: View {
    var body: some View {
        Text("Settings")
            .navigationTitle("Settings")
    }
}
```

## Deep Linking

Handle URLs to navigate directly to specific screens.

### Bad

```swift
// Scattered URL handling with string matching
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onOpenURL { url in
                    // Messy string parsing everywhere
                    if url.absoluteString.contains("user") {
                        // Somehow navigate... but how?
                        NotificationCenter.default.post(
                            name: .navigateToUser,
                            object: nil
                        )
                    }
                }
        }
    }
}

// Views listening to notifications - hard to track
struct SomeView: View {
    var body: some View {
        Text("...")
            .onReceive(NotificationCenter.default.publisher(for: .navigateToUser)) { _ in
                // Complex state management
            }
    }
}
```

### Good

```swift
@Observable
final class NavigationManager {
    var path = NavigationPath()

    func handleDeepLink(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let host = components.host else {
            return
        }

        let pathSegments = components.path.split(separator: "/").map(String.init)
        let queryItems = components.queryItems ?? []

        // Reset to root before deep linking
        path = NavigationPath()

        switch host {
        case "user":
            if let userIdString = pathSegments.first,
               let userId = Int(userIdString) {
                path.append(Route.userDetail(userId: userId))
            }

        case "order":
            path.append(Route.orderHistory)
            if let orderId = pathSegments.first {
                path.append(Route.orderDetail(orderId: orderId))
            }

        case "settings":
            path.append(Route.settings)

        default:
            break
        }
    }

    func popToRoot() {
        path = NavigationPath()
    }

    func pop() {
        guard !path.isEmpty else { return }
        path.removeLast()
    }
}

@main
struct MyApp: App {
    @State private var navigationManager = NavigationManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(navigationManager)
                .onOpenURL { url in
                    navigationManager.handleDeepLink(url)
                }
        }
    }
}

struct ContentView: View {
    @Environment(NavigationManager.self) private var navigationManager

    var body: some View {
        @Bindable var nav = navigationManager

        NavigationStack(path: $nav.path) {
            HomeView()
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .userDetail(let userId):
                        UserDetailView(userId: userId)
                    case .settings:
                        SettingsView()
                    case .orderHistory:
                        OrderHistoryView()
                    case .orderDetail(let orderId):
                        OrderDetailView(orderId: orderId)
                    }
                }
        }
    }
}

// Example deep link URLs:
// myapp://user/42         -> Opens user detail for user 42
// myapp://order/ORD-001   -> Opens order history, then order detail
// myapp://settings        -> Opens settings
```

## Sheet and FullScreen Presentation

Modal presentations with proper state management.

### Bad

```swift
// Single boolean trying to manage multiple modals
struct ProfileView: View {
    @State private var showModal = false
    @State private var modalType: String = ""

    var body: some View {
        VStack {
            Button("Edit Profile") {
                modalType = "edit"
                showModal = true
            }
            Button("Settings") {
                modalType = "settings"
                showModal = true
            }
        }
        .sheet(isPresented: $showModal) {
            // Fragile switch on string
            if modalType == "edit" {
                EditProfileView()
            } else if modalType == "settings" {
                SettingsView()
            }
        }
    }
}
```

### Good

```swift
struct ProfileView: View {
    @State private var showingEditProfile = false
    @State private var showingSettings = false
    @State private var showingFullScreenPhoto = false

    var body: some View {
        VStack(spacing: 20) {
            Button("Edit Profile") {
                showingEditProfile = true
            }

            Button("Settings") {
                showingSettings = true
            }

            Button("View Photo") {
                showingFullScreenPhoto = true
            }
        }
        .sheet(isPresented: $showingEditProfile) {
            EditProfileView()
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView()
        }
        .fullScreenCover(isPresented: $showingFullScreenPhoto) {
            PhotoDetailView()
        }
    }
}

struct EditProfileView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                TextField("Name", text: .constant(""))
            }
            .navigationTitle("Edit Profile")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        // Save changes
                        dismiss()
                    }
                }
            }
        }
    }
}

struct PhotoDetailView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack(alignment: .topTrailing) {
            Color.black.ignoresSafeArea()

            Image(systemName: "photo")
                .resizable()
                .scaledToFit()

            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.title)
                    .foregroundStyle(.white)
            }
            .padding()
        }
    }
}
```

## Item-Based Presentation

Present sheets based on optional item selection.

### Bad

```swift
struct OrderListView: View {
    @State private var orders: [Order] = []
    @State private var showingDetail = false
    @State private var selectedOrderId: String?  // Separate state to track

    var body: some View {
        List(orders) { order in
            Button(order.title) {
                selectedOrderId = order.id  // Must sync manually
                showingDetail = true
            }
        }
        .sheet(isPresented: $showingDetail) {
            // Must find the order again
            if let id = selectedOrderId,
               let order = orders.first(where: { $0.id == id }) {
                OrderDetailSheet(order: order)
            }
        }
    }
}
```

### Good

```swift
struct Order: Identifiable {
    let id: String
    let title: String
    let amount: Decimal
    let date: Date
}

struct OrderListView: View {
    @State private var orders: [Order] = [
        Order(id: "ORD-001", title: "Office Supplies", amount: 149.99, date: .now),
        Order(id: "ORD-002", title: "Electronics", amount: 899.00, date: .now.addingTimeInterval(-86400)),
        Order(id: "ORD-003", title: "Furniture", amount: 1299.00, date: .now.addingTimeInterval(-172800))
    ]

    @State private var selectedOrder: Order?

    var body: some View {
        NavigationStack {
            List(orders) { order in
                Button {
                    selectedOrder = order
                } label: {
                    OrderRow(order: order)
                }
            }
            .navigationTitle("Orders")
            .sheet(item: $selectedOrder) { order in
                OrderDetailSheet(order: order)
            }
        }
    }
}

struct OrderRow: View {
    let order: Order

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(order.title)
                    .font(.headline)
                Text(order.id)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(order.amount, format: .currency(code: "USD"))
        }
    }
}

struct OrderDetailSheet: View {
    let order: Order
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section("Order Info") {
                    LabeledContent("Order ID", value: order.id)
                    LabeledContent("Title", value: order.title)
                    LabeledContent("Amount") {
                        Text(order.amount, format: .currency(code: "USD"))
                    }
                    LabeledContent("Date") {
                        Text(order.date, style: .date)
                    }
                }
            }
            .navigationTitle("Order Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
```

## Coordinator Pattern for Complex Flows

Manage multi-step flows with a coordinator.

### Bad

```swift
// Scattered navigation logic across views
struct OnboardingView: View {
    @State private var currentPage = 0
    @AppStorage("hasCompletedOnboarding") private var completed = false

    var body: some View {
        TabView(selection: $currentPage) {
            WelcomeView(onNext: { currentPage = 1 })
                .tag(0)
            ProfileSetupView(onNext: { currentPage = 2 }, onBack: { currentPage = 0 })
                .tag(1)
            PreferencesView(onComplete: { completed = true })
                .tag(2)
        }
    }
}

// Each view manages its own navigation - hard to track flow
struct WelcomeView: View {
    var onNext: () -> Void

    var body: some View {
        Button("Next", action: onNext)
    }
}
```

### Good

```swift
@Observable
final class OnboardingCoordinator {
    enum Step: CaseIterable {
        case welcome
        case profile
        case preferences
        case complete
    }

    var currentStep: Step = .welcome

    // Collected data
    var userName: String = ""
    var email: String = ""
    var notificationsEnabled: Bool = true
    var theme: String = "system"

    var canGoBack: Bool {
        currentStep != .welcome
    }

    var progress: Double {
        let steps = Step.allCases
        guard let index = steps.firstIndex(of: currentStep) else { return 0 }
        return Double(index) / Double(steps.count - 1)
    }

    func next() {
        switch currentStep {
        case .welcome:
            currentStep = .profile
        case .profile:
            currentStep = .preferences
        case .preferences:
            currentStep = .complete
        case .complete:
            break
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

    func skip() {
        currentStep = .complete
    }
}

struct OnboardingFlow: View {
    @State private var coordinator = OnboardingCoordinator()
    var onComplete: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Progress indicator
            ProgressView(value: coordinator.progress)
                .padding(.horizontal)

            // Current step content
            Group {
                switch coordinator.currentStep {
                case .welcome:
                    WelcomeStepView(coordinator: coordinator)
                case .profile:
                    ProfileStepView(coordinator: coordinator)
                case .preferences:
                    PreferencesStepView(coordinator: coordinator)
                case .complete:
                    CompleteStepView(onFinish: onComplete)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .animation(.easeInOut, value: coordinator.currentStep)
        }
    }
}

struct WelcomeStepView: View {
    @Bindable var coordinator: OnboardingCoordinator

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "hand.wave.fill")
                .font(.system(size: 80))
                .foregroundStyle(.blue)

            Text("Welcome!")
                .font(.largeTitle.bold())

            Text("Let's get you set up in just a few steps.")
                .font(.title3)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Spacer()

            Button("Get Started") {
                coordinator.next()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Button("Skip Setup") {
                coordinator.skip()
            }
            .foregroundStyle(.secondary)
        }
        .padding()
    }
}

struct ProfileStepView: View {
    @Bindable var coordinator: OnboardingCoordinator

    var body: some View {
        VStack(spacing: 24) {
            Text("Your Profile")
                .font(.title.bold())

            VStack(spacing: 16) {
                TextField("Name", text: $coordinator.userName)
                    .textFieldStyle(.roundedBorder)

                TextField("Email", text: $coordinator.email)
                    .textFieldStyle(.roundedBorder)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
            }
            .padding(.horizontal)

            Spacer()

            HStack {
                Button("Back") {
                    coordinator.back()
                }
                .buttonStyle(.bordered)

                Button("Continue") {
                    coordinator.next()
                }
                .buttonStyle(.borderedProminent)
            }
            .controlSize(.large)
        }
        .padding()
    }
}

struct PreferencesStepView: View {
    @Bindable var coordinator: OnboardingCoordinator

    var body: some View {
        VStack(spacing: 24) {
            Text("Preferences")
                .font(.title.bold())

            Form {
                Toggle("Enable Notifications", isOn: $coordinator.notificationsEnabled)

                Picker("Theme", selection: $coordinator.theme) {
                    Text("System").tag("system")
                    Text("Light").tag("light")
                    Text("Dark").tag("dark")
                }
            }
            .scrollContentBackground(.hidden)

            Spacer()

            HStack {
                Button("Back") {
                    coordinator.back()
                }
                .buttonStyle(.bordered)

                Button("Finish") {
                    coordinator.next()
                }
                .buttonStyle(.borderedProminent)
            }
            .controlSize(.large)
        }
        .padding()
    }
}

struct CompleteStepView: View {
    var onFinish: () -> Void

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 80))
                .foregroundStyle(.green)

            Text("You're All Set!")
                .font(.largeTitle.bold())

            Text("Your account is ready to use.")
                .font(.title3)
                .foregroundStyle(.secondary)

            Spacer()

            Button("Let's Go") {
                onFinish()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding()
    }
}

// Usage in App
@main
struct MyApp: App {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false

    var body: some Scene {
        WindowGroup {
            if hasCompletedOnboarding {
                ContentView()
            } else {
                OnboardingFlow {
                    hasCompletedOnboarding = true
                }
            }
        }
    }
}
```

## Navigation State Persistence

Save and restore navigation state across app launches.

### Bad

```swift
// No persistence - user loses their place on restart
struct ContentView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            HomeView(path: $path)
        }
        // Navigation resets on every launch
    }
}
```

### Good

```swift
// Codable route for persistence
enum Route: Hashable, Codable {
    case userDetail(userId: Int)
    case settings
    case orderHistory
    case orderDetail(orderId: String)
}

@Observable
final class NavigationManager {
    var path = NavigationPath()

    private let saveKey = "navigation_path"

    init() {
        loadPath()
    }

    func savePath() {
        guard let representation = path.codable else { return }

        do {
            let data = try JSONEncoder().encode(representation)
            UserDefaults.standard.set(data, forKey: saveKey)
        } catch {
            print("Failed to save navigation path: \(error)")
        }
    }

    func loadPath() {
        guard let data = UserDefaults.standard.data(forKey: saveKey) else { return }

        do {
            let representation = try JSONDecoder().decode(
                NavigationPath.CodableRepresentation.self,
                from: data
            )
            path = NavigationPath(representation)
        } catch {
            print("Failed to load navigation path: \(error)")
        }
    }

    func clearSavedPath() {
        UserDefaults.standard.removeObject(forKey: saveKey)
    }
}

@main
struct MyApp: App {
    @State private var navigationManager = NavigationManager()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(navigationManager)
                .onChange(of: scenePhase) { oldPhase, newPhase in
                    if newPhase == .inactive {
                        navigationManager.savePath()
                    }
                }
        }
    }
}

struct ContentView: View {
    @Environment(NavigationManager.self) private var navigationManager

    var body: some View {
        @Bindable var nav = navigationManager

        NavigationStack(path: $nav.path) {
            HomeView()
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .userDetail(let userId):
                        UserDetailView(userId: userId)
                    case .settings:
                        SettingsView()
                    case .orderHistory:
                        OrderHistoryView()
                    case .orderDetail(let orderId):
                        OrderDetailView(orderId: orderId)
                    }
                }
        }
    }
}

struct HomeView: View {
    @Environment(NavigationManager.self) private var navigationManager

    var body: some View {
        List {
            Section {
                NavigationLink(value: Route.userDetail(userId: 1)) {
                    Label("Profile", systemImage: "person")
                }

                NavigationLink(value: Route.orderHistory) {
                    Label("Orders", systemImage: "bag")
                }

                NavigationLink(value: Route.settings) {
                    Label("Settings", systemImage: "gear")
                }
            }

            Section {
                Button("Clear Navigation History") {
                    navigationManager.clearSavedPath()
                }
                .foregroundStyle(.red)
            }
        }
        .navigationTitle("Home")
    }
}

struct UserDetailView: View {
    let userId: Int

    var body: some View {
        List {
            Text("User ID: \(userId)")
            NavigationLink("View Orders", value: Route.orderHistory)
        }
        .navigationTitle("User \(userId)")
    }
}

struct OrderHistoryView: View {
    let orderIds = ["ORD-001", "ORD-002", "ORD-003"]

    var body: some View {
        List(orderIds, id: \.self) { orderId in
            NavigationLink(orderId, value: Route.orderDetail(orderId: orderId))
        }
        .navigationTitle("Order History")
    }
}

struct OrderDetailView: View {
    let orderId: String

    var body: some View {
        Text("Order: \(orderId)")
            .navigationTitle(orderId)
    }
}

struct SettingsView: View {
    var body: some View {
        List {
            Text("Settings content")
        }
        .navigationTitle("Settings")
    }
}
```

## Complete Navigation Example

A full example combining all patterns.

```swift
import SwiftUI

// MARK: - Routes

enum Route: Hashable, Codable {
    case userDetail(userId: Int)
    case settings
    case orderHistory
    case orderDetail(orderId: String)
    case search
}

// MARK: - Navigation Manager

@Observable
final class AppNavigationManager {
    var path = NavigationPath()
    var showingSearch = false
    var selectedOrder: Order?

    private let saveKey = "app_navigation"

    init() {
        loadPath()
    }

    func handleDeepLink(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let host = components.host else {
            return
        }

        let pathSegments = components.path.split(separator: "/").map(String.init)

        path = NavigationPath()

        switch host {
        case "user":
            if let idString = pathSegments.first, let id = Int(idString) {
                path.append(Route.userDetail(userId: id))
            }
        case "order":
            path.append(Route.orderHistory)
            if let orderId = pathSegments.first {
                path.append(Route.orderDetail(orderId: orderId))
            }
        case "settings":
            path.append(Route.settings)
        case "search":
            showingSearch = true
        default:
            break
        }
    }

    func navigate(to route: Route) {
        path.append(route)
    }

    func popToRoot() {
        path = NavigationPath()
    }

    func savePath() {
        guard let representation = path.codable else { return }
        if let data = try? JSONEncoder().encode(representation) {
            UserDefaults.standard.set(data, forKey: saveKey)
        }
    }

    func loadPath() {
        guard let data = UserDefaults.standard.data(forKey: saveKey),
              let representation = try? JSONDecoder().decode(
                  NavigationPath.CodableRepresentation.self,
                  from: data
              ) else {
            return
        }
        path = NavigationPath(representation)
    }
}

// MARK: - App Entry

@main
struct NavigationDemoApp: App {
    @State private var navigationManager = AppNavigationManager()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            MainView()
                .environment(navigationManager)
                .onOpenURL { url in
                    navigationManager.handleDeepLink(url)
                }
                .onChange(of: scenePhase) { _, newPhase in
                    if newPhase == .inactive {
                        navigationManager.savePath()
                    }
                }
        }
    }
}

// MARK: - Main View

struct MainView: View {
    @Environment(AppNavigationManager.self) private var nav

    var body: some View {
        @Bindable var navigation = nav

        NavigationStack(path: $navigation.path) {
            MainMenuView()
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .userDetail(let userId):
                        UserProfileView(userId: userId)
                    case .settings:
                        AppSettingsView()
                    case .orderHistory:
                        OrderListView()
                    case .orderDetail(let orderId):
                        OrderView(orderId: orderId)
                    case .search:
                        SearchView()
                    }
                }
        }
        .sheet(isPresented: $navigation.showingSearch) {
            SearchView()
        }
        .sheet(item: $navigation.selectedOrder) { order in
            OrderSheet(order: order)
        }
    }
}

// MARK: - Views

struct MainMenuView: View {
    @Environment(AppNavigationManager.self) private var nav

    var body: some View {
        List {
            NavigationLink(value: Route.userDetail(userId: 1)) {
                Label("My Profile", systemImage: "person.circle")
            }

            NavigationLink(value: Route.orderHistory) {
                Label("My Orders", systemImage: "bag")
            }

            NavigationLink(value: Route.settings) {
                Label("Settings", systemImage: "gear")
            }

            Button {
                nav.showingSearch = true
            } label: {
                Label("Search", systemImage: "magnifyingglass")
            }
        }
        .navigationTitle("My App")
    }
}

struct UserProfileView: View {
    let userId: Int

    var body: some View {
        List {
            Section("Account") {
                Text("User ID: \(userId)")
                Text("Member since 2024")
            }

            Section {
                NavigationLink("Order History", value: Route.orderHistory)
                NavigationLink("Settings", value: Route.settings)
            }
        }
        .navigationTitle("Profile")
    }
}

struct OrderListView: View {
    @Environment(AppNavigationManager.self) private var nav

    let orders = [
        Order(id: "ORD-001", title: "Electronics", amount: 299.99, date: .now),
        Order(id: "ORD-002", title: "Books", amount: 45.00, date: .now),
        Order(id: "ORD-003", title: "Clothing", amount: 89.99, date: .now)
    ]

    var body: some View {
        List(orders) { order in
            Button {
                nav.selectedOrder = order
            } label: {
                OrderRowView(order: order)
            }
        }
        .navigationTitle("Orders")
    }
}

struct OrderRowView: View {
    let order: Order

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(order.title)
                Text(order.id)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(order.amount, format: .currency(code: "USD"))
        }
    }
}

struct OrderView: View {
    let orderId: String

    var body: some View {
        Text("Order \(orderId)")
            .navigationTitle(orderId)
    }
}

struct OrderSheet: View {
    let order: Order
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                LabeledContent("ID", value: order.id)
                LabeledContent("Title", value: order.title)
                LabeledContent("Amount") {
                    Text(order.amount, format: .currency(code: "USD"))
                }
            }
            .navigationTitle("Order Details")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
        .presentationDetents([.medium])
    }
}

struct AppSettingsView: View {
    var body: some View {
        List {
            Section("Appearance") {
                Text("Theme")
                Text("App Icon")
            }
            Section("Account") {
                Text("Notifications")
                Text("Privacy")
            }
        }
        .navigationTitle("Settings")
    }
}

struct SearchView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var query = ""

    var body: some View {
        NavigationStack {
            List {
                Text("Search results for: \(query)")
            }
            .searchable(text: $query)
            .navigationTitle("Search")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }
}

// MARK: - Model

struct Order: Identifiable, Hashable {
    let id: String
    let title: String
    let amount: Decimal
    let date: Date
}
```

## Key Patterns Summary

| Pattern | Use Case | Key Components |
|---------|----------|----------------|
| NavigationStack + Path | Programmatic navigation | `NavigationPath`, `navigationDestination(for:)` |
| Deep Linking | External URL handling | `onOpenURL`, URL parsing |
| Sheet | Modal content | `.sheet(isPresented:)` |
| FullScreenCover | Immersive modal | `.fullScreenCover(isPresented:)` |
| Item-Based Sheet | Selection-driven modal | `.sheet(item:)` |
| Coordinator | Multi-step flows | `@Observable` coordinator class |
| Persistence | State restoration | `NavigationPath.CodableRepresentation` |
