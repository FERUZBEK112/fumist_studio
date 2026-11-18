import XCTest

final class StudioTests: XCTestCase {
    func testEditorStaysInsideApp() {
        let app = XCUIApplication()
        app.launch()
        let web = app.webViews.firstMatch
        XCTAssertTrue(web.waitForExistence(timeout: 20))
        XCTAssertTrue(web.buttons.firstMatch.waitForExistence(timeout: 90))
        XCTAssertEqual(app.state, .runningForeground)
    }
}
