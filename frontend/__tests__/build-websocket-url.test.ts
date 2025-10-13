import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { buildWebSocketUrl } from "#/utils/websocket-url";

describe("buildWebSocketUrl", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("Basic URL construction", () => {
    it("should build WebSocket URL with conversation ID, URL, and session key", () => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "localhost:3000",
      });

      const result = buildWebSocketUrl(
        "conv-123",
        "http://localhost:8080/api/conversations/conv-123",
        "session-key-abc",
      );

      expect(result).toBe(
        "ws://localhost:8080/sockets/events/conv-123?session_api_key=session-key-abc",
      );
    });

    it("should use wss:// protocol when window.location.protocol is https:", () => {
      vi.stubGlobal("location", {
        protocol: "https:",
        host: "localhost:3000",
      });

      const result = buildWebSocketUrl(
        "conv-123",
        "https://example.com:8080/api/conversations/conv-123",
        "session-key-abc",
      );

      expect(result).toBe(
        "wss://example.com:8080/sockets/events/conv-123?session_api_key=session-key-abc",
      );
    });

    it("should extract host and port from conversation URL", () => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "localhost:3000",
      });

      const result = buildWebSocketUrl(
        "conv-456",
        "http://agent-server.com:9000/api/conversations/conv-456",
        null,
      );

      expect(result).toBe("ws://agent-server.com:9000/sockets/events/conv-456");
    });
  });

  describe("Session API key handling", () => {
    beforeEach(() => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "localhost:3000",
      });
    });

    it("should include session_api_key query parameter when provided", () => {
      const result = buildWebSocketUrl(
        "conv-123",
        "http://localhost:8080/api/conversations/conv-123",
        "my-secret-key",
      );

      expect(result).toContain("?session_api_key=my-secret-key");
    });

    it("should not include session_api_key query parameter when null", () => {
      const result = buildWebSocketUrl(
        "conv-123",
        "http://localhost:8080/api/conversations/conv-123",
        null,
      );

      expect(result).toBe("ws://localhost:8080/sockets/events/conv-123");
      expect(result).not.toContain("session_api_key");
    });

    it("should not include session_api_key query parameter when undefined", () => {
      const result = buildWebSocketUrl(
        "conv-123",
        "http://localhost:8080/api/conversations/conv-123",
        undefined,
      );

      expect(result).toBe("ws://localhost:8080/sockets/events/conv-123");
      expect(result).not.toContain("session_api_key");
    });
  });

  describe("Fallback to window.location.host", () => {
    it("should use window.location.host when conversation URL is null", () => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "fallback-host:4000",
      });

      const result = buildWebSocketUrl("conv-123", null, null);

      expect(result).toBe("ws://fallback-host:4000/sockets/events/conv-123");
    });

    it("should use window.location.host when conversation URL is undefined", () => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "fallback-host:4000",
      });

      const result = buildWebSocketUrl("conv-123", undefined, null);

      expect(result).toBe("ws://fallback-host:4000/sockets/events/conv-123");
    });

    it("should use window.location.host when conversation URL is relative path", () => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "fallback-host:4000",
      });

      const result = buildWebSocketUrl(
        "conv-123",
        "/api/conversations/conv-123",
        null,
      );

      expect(result).toBe("ws://fallback-host:4000/sockets/events/conv-123");
    });

    it("should use window.location.host when conversation URL is invalid", () => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "fallback-host:4000",
      });

      const result = buildWebSocketUrl("conv-123", "not-a-valid-url", null);

      expect(result).toBe("ws://fallback-host:4000/sockets/events/conv-123");
    });
  });

  describe("Edge cases", () => {
    beforeEach(() => {
      vi.stubGlobal("location", {
        protocol: "http:",
        host: "localhost:3000",
      });
    });

    it("should return null when conversationId is undefined", () => {
      const result = buildWebSocketUrl(
        undefined,
        "http://localhost:8080/api/conversations/conv-123",
        "session-key",
      );

      expect(result).toBeNull();
    });

    it("should return null when conversationId is empty string", () => {
      const result = buildWebSocketUrl(
        "",
        "http://localhost:8080/api/conversations/conv-123",
        "session-key",
      );

      expect(result).toBeNull();
    });

    it("should handle conversation URLs with non-standard ports", () => {
      const result = buildWebSocketUrl(
        "conv-123",
        "http://example.com:12345/api/conversations/conv-123",
        null,
      );

      expect(result).toBe("ws://example.com:12345/sockets/events/conv-123");
    });

    it("should handle conversation URLs without port (default port)", () => {
      const result = buildWebSocketUrl(
        "conv-123",
        "http://example.com/api/conversations/conv-123",
        null,
      );

      expect(result).toBe("ws://example.com/sockets/events/conv-123");
    });

    it("should handle conversation IDs with special characters", () => {
      const result = buildWebSocketUrl(
        "conv-123-abc_def",
        "http://localhost:8080/api/conversations/conv-123-abc_def",
        null,
      );

      expect(result).toBe(
        "ws://localhost:8080/sockets/events/conv-123-abc_def",
      );
    });

    it("should handle session keys with special characters", () => {
      const result = buildWebSocketUrl(
        "conv-123",
        "http://localhost:8080/api/conversations/conv-123",
        "key-with-special_chars.123",
      );

      expect(result).toContain("?session_api_key=key-with-special_chars.123");
    });
  });
});
