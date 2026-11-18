import SwiftUI
import SafariServices

@main
struct FumistStudio: App {
    var body: some Scene {
        WindowGroup {
            VStack(spacing: 24) {
                Text("FUMIST Studio").font(.largeTitle.bold())
                Button("Montajni ochish") { showStudio = true }
            }.sheet(isPresented: $showStudio) { StudioBrowser() }
        }
    }
    @State private var showStudio = true
}
private let studioURL = URL(string: "https://fumist-studio-production.up.railway.app/mobile-releases/1.3.1/index.html")!
private struct StudioBrowser: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: studioURL)
    }
    func updateUIViewController(_ controller: SFSafariViewController, context: Context) {}
}
