import { act, renderHook } from "@testing-library/react";
import { describe, it, vi } from "vitest";
import { useTyping } from "./useTyping";

vi.useFakeTimers();

describe("useTyping", () => {
  it("should 'type' a given message", () => {
    const text = "Hello, World!";
    const typingSpeed = 10;

    const { result } = renderHook(() => useTyping(text));
    expect(result.current).toBe("H");

    act(() => {
      vi.advanceTimersByTime(typingSpeed);
    });

    expect(result.current).toBe("He");

    act(() => {
      vi.advanceTimersByTime(typingSpeed);
    });

    expect(result.current).toBe("Hel");

    for (let i = 3; i < text.length; i += 1) {
      act(() => {
        vi.advanceTimersByTime(typingSpeed);
      });
    }

    expect(result.current).toBe("Hello, World!");

    act(() => {
      vi.advanceTimersByTime(typingSpeed);
    });

    expect(result.current).toBe("Hello, World!");
  });
});
