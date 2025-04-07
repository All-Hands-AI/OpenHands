import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { trackError, showErrorToast, showChatError } from "#/utils/error-handler";
import posthog from "posthog-js";
import toast from "react-hot-toast";
import * as Actions from "#/services/actions";

vi.mock("posthog-js", () => ({
  default: {
    captureException: vi.fn(),
  },
}));

vi.mock("react-hot-toast", () => ({
  default: {
    error: vi.fn(),
  },
}));

vi.mock("#/services/actions", () => ({
  handleStatusMessage: vi.fn(),
}));

describe("Error Handler", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("trackError", () => {
    it("should send error to PostHog with basic info", () => {
      const error = {
        message: "Test error",
        source: "test",
      };

      trackError(error);

      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Test error"), {
        error_source: "test",
      });
    });

    it("should include additional metadata in PostHog event", () => {
      const error = {
        message: "Test error",
        source: "test",
        metadata: {
          extra: "info",
          details: { foo: "bar" },
        },
      };

      trackError(error);

      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Test error"), {
        error_source: "test",
        extra: "info",
        details: { foo: "bar" },
      });
    });
  });

  describe("showErrorToast", () => {
    it("should log error and show toast", () => {
      const error = {
        message: "Toast error",
        source: "toast-test",
      };

      showErrorToast(error);

      // Verify PostHog logging
      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Toast error"), {
        error_source: "toast-test",
      });

      // Verify toast was shown
      expect(toast.error).toHaveBeenCalled();
    });

    it("should include metadata in PostHog event when showing toast", () => {
      const error = {
        message: "Toast error",
        source: "toast-test",
        metadata: { context: "testing" },
      };

      showErrorToast(error);

      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Toast error"), {
        error_source: "toast-test",
        context: "testing",
      });
    });

    it("should log errors from different sources with appropriate metadata", () => {
      // Test agent status error
      showErrorToast({
        message: "Agent error",
        source: "agent-status",
        metadata: { id: "error.agent" },
      });

      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Agent error"), {
        error_source: "agent-status",
        id: "error.agent",
      });

      showErrorToast({
        message: "Server error",
        source: "server",
        metadata: { error_code: 500, details: "Internal error" },
      });

      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Server error"), {
        error_source: "server",
        error_code: 500,
        details: "Internal error",
      });
    });

    it("should log feedback submission errors with conversation context", () => {
      const error = new Error("Feedback submission failed");
      showErrorToast({
        message: error.message,
        source: "feedback",
        metadata: { conversationId: "123", error },
      });

      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Feedback submission failed"), {
        error_source: "feedback",
        conversationId: "123",
        error,
      });
    });
  });

  describe("showChatError", () => {
    it("should log error and show chat error message", () => {
      const error = {
        message: "Chat error",
        source: "chat-test",
        msgId: "123",
      };

      showChatError(error);

      // Verify PostHog logging
      expect(posthog.captureException).toHaveBeenCalledWith(new Error("Chat error"), {
        error_source: "chat-test",
      });

      // Verify error message was shown in chat
      expect(Actions.handleStatusMessage).toHaveBeenCalledWith({
        type: "error",
        message: "Chat error",
        id: "123",
        status_update: true,
      });
    });
  });
});
