import { describe, it, expect, vi, beforeEach } from "vitest";
import ActionType from "#/types/action-type";
import { ActionMessage } from "#/types/message";

// Mock the store and actions
const mockDispatch = vi.fn();
const mockAppendInput = vi.fn();
const mockAppendJupyterInput = vi.fn();

vi.mock("#/store", () => ({
  default: {
    dispatch: mockDispatch,
  },
}));

vi.mock("#/state/command-slice", () => ({
  appendInput: mockAppendInput,
}));

vi.mock("#/state/jupyter-slice", () => ({
  appendJupyterInput: mockAppendJupyterInput,
}));

describe("handleActionMessage", () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  it("should handle RUN actions by adding input to terminal", async () => {
    const { handleActionMessage } = await import("#/services/actions");

    const runAction: ActionMessage = {
      id: 1,
      source: "agent",
      action: ActionType.RUN,
      args: {
        command: "ls -la",
      },
      message: "Running command: ls -la",
      timestamp: "2023-01-01T00:00:00Z",
    };

    // Handle the action
    handleActionMessage(runAction);

    // Check that appendInput was called with the command
    expect(mockDispatch).toHaveBeenCalledWith(mockAppendInput("ls -la"));
    expect(mockAppendJupyterInput).not.toHaveBeenCalled();
  });

  it("should handle RUN_IPYTHON actions by adding input to Jupyter", async () => {
    const { handleActionMessage } = await import("#/services/actions");

    const ipythonAction: ActionMessage = {
      id: 2,
      source: "agent",
      action: ActionType.RUN_IPYTHON,
      args: {
        code: "print('Hello from Jupyter!')",
      },
      message: "Running Python code interactively: print('Hello from Jupyter!')",
      timestamp: "2023-01-01T00:00:00Z",
    };

    // Handle the action
    handleActionMessage(ipythonAction);

    // Check that appendJupyterInput was called with the code
    expect(mockDispatch).toHaveBeenCalledWith(mockAppendJupyterInput("print('Hello from Jupyter!')"));
    expect(mockAppendInput).not.toHaveBeenCalled();
  });

  it("should not process hidden actions", async () => {
    const { handleActionMessage } = await import("#/services/actions");

    const hiddenAction: ActionMessage = {
      id: 3,
      source: "agent",
      action: ActionType.RUN,
      args: {
        command: "secret command",
        hidden: "true",
      },
      message: "Running command: secret command",
      timestamp: "2023-01-01T00:00:00Z",
    };

    // Handle the action
    handleActionMessage(hiddenAction);

    // Check that nothing was dispatched
    expect(mockDispatch).not.toHaveBeenCalled();
  });
});
