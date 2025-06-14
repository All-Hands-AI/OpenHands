import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleActionMessage } from "#/services/actions";
import { appendJupyterInput } from "#/state/jupyter-slice";
import ActionType from "#/types/action-type";
import store from "#/store";

// Mock the store dispatch
vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

// Mock the jupyter slice
vi.mock("#/state/jupyter-slice", () => ({
  appendJupyterInput: vi.fn(),
}));

describe("handleActionMessage - Jupyter Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should dispatch appendJupyterInput when receiving RUN_IPYTHON action", () => {
    const mockMessage = {
      action: ActionType.RUN_IPYTHON,
      args: {
        code: "print('Hello, World!')",
      },
    };

    handleActionMessage(mockMessage);

    expect(appendJupyterInput).toHaveBeenCalledWith("print('Hello, World!')");
    expect(store.dispatch).toHaveBeenCalledWith(appendJupyterInput("print('Hello, World!')"));
  });

  it("should not dispatch appendJupyterInput for other action types", () => {
    const mockMessage = {
      action: ActionType.RUN,
      args: {
        command: "ls -la",
      },
    };

    handleActionMessage(mockMessage);

    expect(appendJupyterInput).not.toHaveBeenCalled();
  });

  it("should not dispatch anything if message is hidden", () => {
    const mockMessage = {
      action: ActionType.RUN_IPYTHON,
      args: {
        code: "print('Hidden message')",
        hidden: true,
      },
    };

    handleActionMessage(mockMessage);

    expect(appendJupyterInput).not.toHaveBeenCalled();
    expect(store.dispatch).not.toHaveBeenCalled();
  });
});