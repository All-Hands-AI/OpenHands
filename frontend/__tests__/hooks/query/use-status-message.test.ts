import { useStatusMessage } from "#/hooks/query/use-status-message";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

// Mock the query-redux-bridge
vi.mock("#/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: vi.fn(),
}));

// Mock console.log and console.warn to avoid cluttering test output
vi.spyOn(console, "log").mockImplementation(() => {});
vi.spyOn(console, "warn").mockImplementation(() => {});

describe("useStatusMessage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with default state when Redux bridge is not available", () => {
    // Mock the bridge to throw an error
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockImplementation(() => {
      throw new Error("Bridge not initialized");
    });

    const { result } = renderHook(() => useStatusMessage());

    expect(result.current.statusMessage.status_update).toBe(true);
    expect(result.current.statusMessage.type).toBe("info");
    expect(result.current.statusMessage.id).toBe("");
    expect(result.current.statusMessage.message).toBe("");
    expect(result.current.isLoading).toBe(false);
  });

  it("should initialize with Redux state when available", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        curStatusMessage: {
          status_update: true,
          type: "info",
          id: "test.id",
          message: "Test message",
        },
      }),
    });

    const { result } = renderHook(() => useStatusMessage());

    expect(result.current.statusMessage.status_update).toBe(true);
    expect(result.current.statusMessage.type).toBe("info");
    expect(result.current.statusMessage.id).toBe("test.id");
    expect(result.current.statusMessage.message).toBe("Test message");
  });

  it("should update status message when setStatusMessage is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        curStatusMessage: {
          status_update: true,
          type: "info",
          id: "",
          message: "",
        },
      }),
    });

    const { result } = renderHook(() => useStatusMessage());

    // Initial state
    expect(result.current.statusMessage.id).toBe("");
    expect(result.current.statusMessage.message).toBe("");

    // Update state
    const newStatusMessage = {
      status_update: true,
      type: "info",
      id: "new.id",
      message: "New message",
    };

    act(() => {
      result.current.setStatusMessage(newStatusMessage);
    });

    // Check updated state
    expect(result.current.statusMessage.id).toBe("new.id");
    expect(result.current.statusMessage.message).toBe("New message");
  });
});