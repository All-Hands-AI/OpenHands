import { renderHook, act } from "@testing-library/react";
import { useScrollToBottom } from "../use-scroll-to-bottom";
import { describe, it, expect, beforeEach, vi } from "vitest";

describe("useScrollToBottom", () => {
  let mockRef: { current: HTMLDivElement | null };
  let mockDom: HTMLDivElement;

  beforeEach(() => {
    mockDom = {
      scrollTop: 0,
      clientHeight: 500,
      scrollHeight: 1000,
      scrollTo: vi.fn(),
    } as unknown as HTMLDivElement;

    mockRef = { current: mockDom };
  });

  it("should auto-scroll when shouldScrollToBottom is true", () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useScrollToBottom(mockRef));

    // Verify initial state
    expect(result.current.autoScroll).toBe(true);
    expect(result.current.hitBottom).toBe(true);

    // Trigger auto-scroll
    act(() => {
      result.current.scrollDomToBottom();
    });

    // Fast-forward timers
    act(() => {
      vi.runAllTimers();
    });

    // Verify scrollTo was called with correct parameters
    expect(mockDom.scrollTo).toHaveBeenCalledWith({
      top: mockDom.scrollHeight,
      behavior: "smooth",
    });

    vi.useRealTimers();
  });

  it("should update scroll state when user scrolls", () => {
    const { result } = renderHook(() => useScrollToBottom(mockRef));

    // Simulate scroll near bottom
    act(() => {
      mockDom.scrollTop = mockDom.scrollHeight - mockDom.clientHeight - 40;
      result.current.onChatBodyScroll(mockDom);
    });

    // Should be considered at bottom due to threshold
    expect(result.current.hitBottom).toBe(true);
    expect(result.current.autoScroll).toBe(true);

    // Simulate scroll away from bottom
    act(() => {
      mockDom.scrollTop = 0;
      result.current.onChatBodyScroll(mockDom);
    });

    // Should not be at bottom
    expect(result.current.hitBottom).toBe(false);
    expect(result.current.autoScroll).toBe(false);
  });
});
