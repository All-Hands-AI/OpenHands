import { renderHook, act } from "@testing-library/react";
import { useAgentState } from "#/hooks/query/simplified/use-agent-state";
import { AgentState } from "#/types/agent-state";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

// Mock the query-redux-bridge
jest.mock("#/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: jest.fn(),
}));

describe("useAgentState (simplified)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should initialize with default state when Redux bridge is not available", () => {
    // Mock the bridge to throw an error
    (getQueryReduxBridge as jest.Mock).mockImplementation(() => {
      throw new Error("Bridge not initialized");
    });

    const { result } = renderHook(() => useAgentState());

    expect(result.current.curAgentState).toBe(AgentState.LOADING);
    expect(result.current.isLoading).toBe(false);
  });

  it("should initialize with Redux state when available", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as jest.Mock).mockReturnValue({
      getReduxSliceState: jest.fn().mockReturnValue({
        curAgentState: AgentState.READY,
      }),
    });

    const { result } = renderHook(() => useAgentState());

    expect(result.current.curAgentState).toBe(AgentState.READY);
  });

  it("should update state when setCurrentAgentState is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as jest.Mock).mockReturnValue({
      getReduxSliceState: jest.fn().mockReturnValue({
        curAgentState: AgentState.LOADING,
      }),
    });

    const { result } = renderHook(() => useAgentState());

    // Initial state
    expect(result.current.curAgentState).toBe(AgentState.LOADING);

    // Update state
    act(() => {
      result.current.setCurrentAgentState(AgentState.READY);
    });

    // Check updated state
    expect(result.current.curAgentState).toBe(AgentState.READY);
  });
});