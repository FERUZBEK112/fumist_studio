import UIKit
import WebKit

private let editor = URL(string: "https://fumist-studio-production.up.railway.app/mobile-releases/1.3.2/index.html")!

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = StudioController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
}

final class StudioController: UIViewController, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate, UIDocumentPickerDelegate {
    private let web = WKWebView(frame: .zero, configuration: {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        return config
    }())
    private var downloads = [ObjectIdentifier: URL]()
    private var exportFolder: URL?

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        web.navigationDelegate = self
        web.uiDelegate = self
        web.allowsBackForwardNavigationGestures = true
        view.addSubview(web)
        web.translatesAutoresizingMaskIntoConstraints = false
        let guide = view.safeAreaLayoutGuide
        NSLayoutConstraint.activate([web.topAnchor.constraint(equalTo: guide.topAnchor), web.bottomAnchor.constraint(equalTo: guide.bottomAnchor), web.leadingAnchor.constraint(equalTo: guide.leadingAnchor), web.trailingAnchor.constraint(equalTo: guide.trailingAnchor)])
        web.load(URLRequest(url: editor))
    }
    private func internalURL(_ url: URL) -> Bool {
        url.scheme == "https" && url.host == editor.host && (url.port == nil || url.port == 443)
    }
    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else { decisionHandler(.cancel); return }
        if action.shouldPerformDownload && (internalURL(url) || url.scheme == "blob") {
            decisionHandler(.download)
        } else if internalURL(url) || action.targetFrame?.isMainFrame == false {
            decisionHandler(.allow)
        } else {
            decisionHandler(.cancel)
            if ["https","tg"].contains(url.scheme ?? "") { UIApplication.shared.open(url) }
        }
    }
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url, internalURL(url) { web.load(action.request) }
        return nil
    }
    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate = self }
    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        do {
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let file = dir.appendingPathComponent((suggestedFilename as NSString).lastPathComponent)
            downloads[ObjectIdentifier(download)] = file
            completionHandler(file)
        } catch { completionHandler(nil) }
    }
    func downloadDidFinish(_ download: WKDownload) {
        guard let file = downloads.removeValue(forKey: ObjectIdentifier(download)) else { return }
        let picker = UIDocumentPickerViewController(forExporting: [file], asCopy: true)
        picker.delegate = self
        exportFolder = file.deletingLastPathComponent()
        present(picker, animated: true)
    }
    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        if let file = downloads.removeValue(forKey: ObjectIdentifier(download)) { try? FileManager.default.removeItem(at: file.deletingLastPathComponent()) }
        message(error.localizedDescription) {}
    }
    private func cleanExport() {
        if let dir = exportFolder { try? FileManager.default.removeItem(at: dir) }
        exportFolder = nil
    }
    func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) { cleanExport() }
    func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) { cleanExport() }
    private func message(_ text: String, done: @escaping () -> Void) {
        let alert = UIAlertController(title: "FUMIST Studio", message: text, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in done() })
        present(alert, animated: true)
    }
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage text: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) { message(text, done: completionHandler) }
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage text: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = UIAlertController(title: "FUMIST Studio", message: text, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Bekor qilish", style: .cancel) { _ in completionHandler(false) })
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
        present(alert, animated: true)
    }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        if (error as NSError).code == NSURLErrorCancelled { return }
        message("Internet aloqasini tekshirib, qayta urinib ko‘ring.") { self.web.load(URLRequest(url: editor)) }
    }
}
