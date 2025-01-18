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