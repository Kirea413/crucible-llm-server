import Foundation

@MainActor
final class LlamaState {
    func completeForAPI(text: String, maxTokens: Int = 500) async -> String {
        return "日本語テスト"
    }
}

@main
struct HTTPServerHarness {
    @MainActor
    static func main() async throws {
        let state = LlamaState()
        let server = HTTPServer(port: 18080)
        try server.start(llamaState: state)
        try await Task.sleep(nanoseconds: 60_000_000_000)
        withExtendedLifetime(state) {}
        server.stop()
    }
}
