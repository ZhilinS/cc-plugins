# UIKit Interop

## UIViewRepresentable Structure

Wrap UIKit views for use in SwiftUI using `UIViewRepresentable`. Implement `makeUIView` to create the view and `updateUIView` to sync SwiftUI state changes.

```swift
// Bad - trying to recreate complex UIKit functionality in SwiftUI
struct MapView: View {
    let coordinate: CLLocationCoordinate2D
    @State private var region: MKCoordinateRegion

    var body: some View {
        // SwiftUI Map has limited annotation customization
        Map(coordinateRegion: $region, annotationItems: []) { _ in
            // Limited to MapMarker or MapAnnotation
        }
    }
}

// Good - wrap MKMapView for full control
struct MapView: UIViewRepresentable {
    let coordinate: CLLocationCoordinate2D
    var showsUserLocation: Bool = false

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.showsUserLocation = showsUserLocation
        return mapView
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        let region = MKCoordinateRegion(
            center: coordinate,
            span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
        )
        mapView.setRegion(region, animated: true)
    }
}

// Usage in SwiftUI
struct LocationView: View {
    var body: some View {
        MapView(
            coordinate: CLLocationCoordinate2D(latitude: 37.7749, longitude: -122.4194),
            showsUserLocation: true
        )
        .ignoresSafeArea()
    }
}
```

## Coordinator Pattern for Delegates

Use a Coordinator class to handle UIKit delegate callbacks. The Coordinator bridges UIKit's delegate pattern to SwiftUI's declarative model.

```swift
// Bad - no way to handle delegate callbacks
struct ImagePicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        // No delegate set - can't receive selected image
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
}

// Good - Coordinator handles delegate callbacks
struct ImagePicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        picker.sourceType = .photoLibrary
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

// Usage
struct PhotoSelectionView: View {
    @State private var showPicker = false
    @State private var image: UIImage?

    var body: some View {
        VStack {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
            }
            Button("Select Photo") { showPicker = true }
        }
        .sheet(isPresented: $showPicker) {
            ImagePicker(selectedImage: $image)
        }
    }
}
```

## UIViewControllerRepresentable for Full Screens

Wrap entire UIKit view controllers when you need their full functionality. This works for document pickers, mail composers, or any UIKit screen.

```swift
// Bad - trying to build file picker from scratch
struct FilePicker: View {
    var body: some View {
        // No native SwiftUI document picker with full functionality
        List { /* manual file browsing? */ }
    }
}

// Good - wrap UIDocumentPickerViewController
struct DocumentPicker: UIViewControllerRepresentable {
    let contentTypes: [UTType]
    let onPick: (URL) -> Void

    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: contentTypes)
        picker.delegate = context.coordinator
        picker.allowsMultipleSelection = false
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
            guard let url = urls.first else { return }
            onPick(url)
        }
    }
}

// Usage
struct ImportView: View {
    @State private var showPicker = false
    @State private var selectedFile: URL?

    var body: some View {
        VStack {
            if let selectedFile {
                Text("Selected: \(selectedFile.lastPathComponent)")
            }
            Button("Import Document") { showPicker = true }
        }
        .sheet(isPresented: $showPicker) {
            DocumentPicker(contentTypes: [.pdf, .plainText]) { url in
                selectedFile = url
            }
        }
    }
}
```

## When to Drop to UIKit

Use UIKit when SwiftUI lacks the control you need: complex gestures, fine-grained scroll control, specific keyboard behavior, camera/media capture, or when you have well-tested UIKit components.

```swift
// Good reasons to use UIKit:
// - Custom keyboard accessories
// - Text field with specific input behaviors
// - Fine-grained control over first responder

struct AdvancedTextField: UIViewRepresentable {
    @Binding var text: String
    var placeholder: String
    var keyboardType: UIKeyboardType = .default
    var onSubmit: () -> Void = {}

    func makeUIView(context: Context) -> UITextField {
        let textField = UITextField()
        textField.placeholder = placeholder
        textField.keyboardType = keyboardType
        textField.delegate = context.coordinator
        textField.borderStyle = .roundedRect

        // Add toolbar with done button - hard to do in SwiftUI
        let toolbar = UIToolbar()
        toolbar.sizeToFit()
        let flexSpace = UIBarButtonItem(barButtonSystemItem: .flexibleSpace, target: nil, action: nil)
        let doneButton = UIBarButtonItem(
            barButtonSystemItem: .done,
            target: context.coordinator,
            action: #selector(Coordinator.donePressed)
        )
        toolbar.items = [flexSpace, doneButton]
        textField.inputAccessoryView = toolbar

        return textField
    }

    func updateUIView(_ textField: UITextField, context: Context) {
        if textField.text != text {
            textField.text = text
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UITextFieldDelegate {
        var parent: AdvancedTextField

        init(_ parent: AdvancedTextField) {
            self.parent = parent
        }

        func textFieldDidChangeSelection(_ textField: UITextField) {
            parent.text = textField.text ?? ""
        }

        func textFieldShouldReturn(_ textField: UITextField) -> Bool {
            parent.onSubmit()
            textField.resignFirstResponder()
            return true
        }

        @objc func donePressed() {
            UIApplication.shared.sendAction(
                #selector(UIResponder.resignFirstResponder),
                to: nil, from: nil, for: nil
            )
        }
    }
}

// Usage
struct FormView: View {
    @State private var amount = ""

    var body: some View {
        Form {
            AdvancedTextField(
                text: $amount,
                placeholder: "Enter amount",
                keyboardType: .decimalPad
            ) {
                print("Submitted: \(amount)")
            }
        }
    }
}
```

## Avoiding Retain Cycles

Coordinators hold a reference to their parent representable. Use `weak` references or closures to prevent retain cycles when the Coordinator stores callbacks.

```swift
// Bad - strong reference can cause retain cycle
struct VideoPlayer: UIViewRepresentable {
    let url: URL
    var onFinish: () -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)  // Coordinator holds strong reference to parent
    }

    class Coordinator: NSObject {
        var parent: VideoPlayer  // Strong reference

        init(parent: VideoPlayer) {
            self.parent = parent
        }

        @objc func playerDidFinish() {
            parent.onFinish()  // If onFinish captures self, cycle forms
        }
    }

    func makeUIView(context: Context) -> UIView { UIView() }
    func updateUIView(_ uiView: UIView, context: Context) {}
}

// Good - use closures in Coordinator instead of parent reference
struct VideoPlayer: UIViewRepresentable {
    let url: URL
    var onFinish: () -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onFinish: onFinish)  // Pass only what's needed
    }

    class Coordinator: NSObject {
        let onFinish: () -> Void

        init(onFinish: @escaping () -> Void) {
            self.onFinish = onFinish
        }

        @objc func playerDidFinish() {
            onFinish()
        }
    }

    func makeUIView(context: Context) -> UIView { UIView() }
    func updateUIView(_ uiView: UIView, context: Context) {}
}

// Good - weak reference when parent reference is needed
struct CameraView: UIViewRepresentable {
    @Binding var capturedImage: UIImage?

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject {
        weak var parent: CameraView?  // Weak reference breaks cycle

        init(_ parent: CameraView) {
            self.parent = parent
        }

        func didCaptureImage(_ image: UIImage) {
            parent?.capturedImage = image
        }
    }

    func makeUIView(context: Context) -> UIView { UIView() }
    func updateUIView(_ uiView: UIView, context: Context) {}
}
```

## Hosting SwiftUI in UIKit

Use `UIHostingController` to embed SwiftUI views in UIKit code. This lets you adopt SwiftUI incrementally in existing UIKit apps.

```swift
// Bad - rewriting entire screens at once
class OldViewController: UIViewController {
    // Trying to convert everything to SwiftUI at once
    // leads to big bang rewrites
}

// Good - embed SwiftUI views incrementally
class ProfileViewController: UIViewController {
    private var user: User

    init(user: User) {
        self.user = user
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func viewDidLoad() {
        super.viewDidLoad()

        // Create SwiftUI view
        let profileCard = ProfileCardView(user: user) { [weak self] in
            self?.handleEditTapped()
        }

        // Wrap in hosting controller
        let hostingController = UIHostingController(rootView: profileCard)
        addChild(hostingController)

        // Add to view hierarchy
        hostingController.view.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(hostingController.view)

        NSLayoutConstraint.activate([
            hostingController.view.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 16),
            hostingController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            hostingController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16)
        ])

        hostingController.didMove(toParent: self)
    }

    private func handleEditTapped() {
        // Handle in UIKit land
        let editVC = EditProfileViewController(user: user)
        navigationController?.pushViewController(editVC, animated: true)
    }
}

// The SwiftUI view being hosted
struct ProfileCardView: View {
    let user: User
    let onEdit: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                AsyncImage(url: user.avatarURL) { image in
                    image.resizable().scaledToFill()
                } placeholder: {
                    Color.gray
                }
                .frame(width: 60, height: 60)
                .clipShape(Circle())

                VStack(alignment: .leading) {
                    Text(user.name).font(.headline)
                    Text(user.email).font(.subheadline).foregroundColor(.secondary)
                }

                Spacer()

                Button("Edit", action: onEdit)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

// Simpler alternative using frame-based layout
class SimpleHostingExample: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()

        let swiftUIView = Text("Hello from SwiftUI")
            .padding()
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(8)

        let hostingController = UIHostingController(rootView: swiftUIView)
        addChild(hostingController)

        hostingController.view.frame = CGRect(x: 20, y: 100, width: 200, height: 50)
        hostingController.view.autoresizingMask = [.flexibleWidth, .flexibleBottomMargin]
        view.addSubview(hostingController.view)

        hostingController.didMove(toParent: self)
    }
}
```
