import { beforeEach, describe, expect, it, vi } from "vitest";
import { handleObservationMessage } from "#/services/observations";
import store from "#/store";
import { ObservationMessage } from "#/types/message";

// Mock dependencies
vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

describe("Observations Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleObservationMessage", () => {
    const createErrorMessage = (): ObservationMessage => ({
      id: 14,
      timestamp: "2025-04-14T13:37:54.451843",
      message: "The action has not been executed.",
      cause: 12,
      observation: "error",
      content: "The action has not been executed.",
      extras: {
        error_id: "",
        metadata: {},
      },
    });

    it("should dispatch error messages exactly once", () => {
      const errorMessage = createErrorMessage();

      handleObservationMessage(errorMessage);

      expect(store.dispatch).toHaveBeenCalledTimes(1);
      expect(store.dispatch).toHaveBeenCalledWith({
        type: "chat/addAssistantObservation",
        payload: expect.objectContaining({
          observation: "error",
          content: "The action has not been executed.",
          source: "user",
          extras: {
            error_id: "",
          },
        }),
      });
    });
  });
});
