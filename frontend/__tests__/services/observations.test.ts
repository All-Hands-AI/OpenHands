import { beforeEach, describe, expect, it, vi } from "vitest";
import { handleObservationMessage } from "#/services/observations";
import store from "#/store";
import { ObservationMessage } from "#/types/message";

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

describe("handleObservationMessage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

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

  it("currently shows error messages only once", () => {
    const errorMessage = createErrorMessage();

    handleObservationMessage(errorMessage);

    // Note: current behavior is as follows.
    // - `The action has not been executed.` appears only once as an observation
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

  it("should only show error message once after fix", () => {
    const errorMessage = createErrorMessage();

    handleObservationMessage(errorMessage);

    // After fix: error message should only appear once as an observation
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
