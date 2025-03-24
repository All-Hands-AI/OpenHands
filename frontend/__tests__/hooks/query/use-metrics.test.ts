import { useMetrics } from "#/hooks/query/use-metrics";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

// Mock the query-redux-bridge
vi.mock("#/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: vi.fn(),
}));

describe("useMetrics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with default state when Redux bridge is not available", () => {
    // Mock the bridge to throw an error
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockImplementation(() => {
      throw new Error("Bridge not initialized");
    });

    const { result } = renderHook(() => useMetrics());

    expect(result.current.metrics.cost).toBe(null);
    expect(result.current.metrics.usage).toBe(null);
    expect(result.current.isLoading).toBe(false);
  });

  it("should initialize with Redux state when available", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        cost: 0.25,
        usage: {
          prompt_tokens: 100,
          completion_tokens: 50,
          total_tokens: 150,
        },
      }),
    });

    const { result } = renderHook(() => useMetrics());

    expect(result.current.metrics.cost).toBe(0.25);
    expect(result.current.metrics.usage?.prompt_tokens).toBe(100);
    expect(result.current.metrics.usage?.completion_tokens).toBe(50);
    expect(result.current.metrics.usage?.total_tokens).toBe(150);
  });

  it("should update metrics when setMetrics is called", () => {
    // Mock the bridge to return a state
    (getQueryReduxBridge as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getReduxSliceState: vi.fn().mockReturnValue({
        cost: null,
        usage: null,
      }),
    });

    const { result } = renderHook(() => useMetrics());

    // Initial state
    expect(result.current.metrics.cost).toBe(null);
    expect(result.current.metrics.usage).toBe(null);

    // Update state
    const newMetrics = {
      cost: 0.5,
      usage: {
        prompt_tokens: 200,
        completion_tokens: 100,
        total_tokens: 300,
      },
    };

    act(() => {
      result.current.setMetrics(newMetrics);
    });

    // Check updated state
    expect(result.current.metrics.cost).toBe(0.5);
    expect(result.current.metrics.usage?.prompt_tokens).toBe(200);
    expect(result.current.metrics.usage?.completion_tokens).toBe(100);
    expect(result.current.metrics.usage?.total_tokens).toBe(300);
  });
});
