import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { logError, showErrorToast, showChatError } from "#/utils/error-handler";
import posthog from "posthog-js";
import toast from "react-hot-toast";
import * as Actions from "#/services/actions";

// Mock dependencies
vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

vi.mock("react-hot-toast", () => ({
  default: {
    custom: vi.fn(),
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

  describe("logError", () => {
    it("should log error to PostHog with basic info", () => {
      const error = {
        message: "Test error",
        source: "test",
      };

      logError(error);

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Test error",
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

      logError(error);

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Test error",
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
      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Toast error",
        error_source: "toast-test",
      });

      // Verify toast was shown
      expect(toast.custom).toHaveBeenCalled();
    });

    it("should include metadata in PostHog event when showing toast", () => {
      const error = {
        message: "Toast error",
        source: "toast-test",
        metadata: { context: "testing" },
      };

      showErrorToast(error);

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Toast error",
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

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Agent error",
        error_source: "agent-status",
        id: "error.agent",
      });

      // Test VSCode error
      showErrorToast({
        message: "VSCode error",
        source: "vscode",
        metadata: { error: "connection failed" },
      });

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "VSCode error",
        error_source: "vscode",
        error: "connection failed",
      });

      // Test server error
      showErrorToast({
        message: "Server error",
        source: "server",
        metadata: { error_code: 500, details: "Internal error" },
      });

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Server error",
        error_source: "server",
        error_code: 500,
        details: "Internal error",
      });
    });

    it("should log query and mutation errors with appropriate metadata", () => {
      // Test query error
      showErrorToast({
        message: "Query failed",
        source: "query",
        metadata: { queryKey: ["users", "123"] },
      });

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Query failed",
        error_source: "query",
        queryKey: ["users", "123"],
      });

      // Test mutation error
      const error = new Error("Mutation failed");
      showErrorToast({
        message: error.message,
        source: "mutation",
        metadata: { error },
      });

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Mutation failed",
        error_source: "mutation",
        error,
      });
    });

    it("should log feedback submission errors with conversation context", () => {
      const error = new Error("Feedback submission failed");
      showErrorToast({
        message: error.message,
        source: "feedback",
        metadata: { conversationId: "123", error },
      });

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Feedback submission failed",
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
      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Chat error",
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

    it("should include metadata in PostHog event when showing chat error", () => {
      const error = {
        message: "Chat error",
        source: "chat-test",
        msgId: "123",
        metadata: {
          context: "chat testing",
          severity: "high",
        },
      };

      showChatError(error);

      expect(posthog.capture).toHaveBeenCalledWith("error_occurred", {
        error_message: "Chat error",
        error_source: "chat-test",
        context: "chat testing",
        severity: "high",
      });
    });
  });
});
