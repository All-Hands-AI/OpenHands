import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useRate } from "#/hooks/use-rate";

describe("useRate", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should initialize", () => {
    const { result } = renderHook(() => useRate());

    expect(result.current.items).toHaveLength(0);
    expect(result.current.rate).toBeNull();
    expect(result.current.lastUpdated).toBeNull();
    expect(result.current.isUnderThreshold).toBe(true);
  });

  it("should handle the case of a single element", () => {
    const { result } = renderHook(() => useRate());

    act(() => {
      result.current.record(123);
    });

    expect(result.current.items).toHaveLength(1);
    expect(result.current.lastUpdated).not.toBeNull();
  });

  it("should return the difference between the last two elements", () => {
    const { result } = renderHook(() => useRate());

    vi.setSystemTime(500);
    act(() => {
      result.current.record(4);
    });

    vi.advanceTimersByTime(500);
    act(() => {
      result.current.record(9);
    });

    expect(result.current.items).toHaveLength(2);
    expect(result.current.rate).toBe(5);
    expect(result.current.lastUpdated).toBe(1000);
  });

  it("should update isUnderThreshold after [threshold]ms of no activity", () => {
    const { result } = renderHook(() => useRate({ threshold: 500 }));

    expect(result.current.isUnderThreshold).toBe(true);

    act(() => {
      // not sure if fake timers is buggy with intervals,
      // but I need to call it twice to register
      vi.advanceTimersToNextTimer();
      vi.advanceTimersToNextTimer();
    });

    expect(result.current.isUnderThreshold).toBe(false);
  });

  it("should return an isUnderThreshold boolean", () => {
    const { result } = renderHook(() => useRate({ threshold: 500 }));

    vi.setSystemTime(500);
    act(() => {
      result.current.record(400);
    });
    act(() => {
      result.current.record(1000);
    });

    expect(result.current.isUnderThreshold).toBe(false);

    act(() => {
      result.current.record(1500);
    });

    expect(result.current.isUnderThreshold).toBe(true);

    act(() => {
      vi.advanceTimersToNextTimer();
      vi.advanceTimersToNextTimer();
    });

    expect(result.current.isUnderThreshold).toBe(false);
  });
});
