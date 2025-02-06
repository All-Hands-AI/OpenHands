import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleStatusMessage } from "#/services/actions";
import store from "#/store";
import { trackError } from "#/utils/error-handler";

// Mock dependencies
vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
    it("should dispatch info messages to status state", () => {
      const message = {
        type: "info",
        message: "Runtime is not available",
        id: "runtime.unavailable",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(store.dispatch).toHaveBeenCalledWith(expect.objectContaining({
        payload: message,
      }));
    });

    it("should log error messages and display them in chat", () => {
      const message = {
        type: "error",
        message: "Runtime connection failed",
        id: "runtime.connection.failed",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(trackError).toHaveBeenCalledWith({
        message: "Runtime connection failed",
        source: "chat",
        metadata: { msgId: "runtime.connection.failed" },
      });

      expect(store.dispatch).toHaveBeenCalledWith(expect.objectContaining({
        payload: message,
      }));
    });
  });
});
