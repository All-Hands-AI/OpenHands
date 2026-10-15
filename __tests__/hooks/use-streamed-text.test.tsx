import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useStreamedText } from "#/hooks/use-streamed-text";

/** Drive `requestAnimationFrame` by hand so the reveal cadence is explicit. */
function manualFrames() {
  let now = 0;
  const callbacks = new Map<number, FrameRequestCallback>();
  let nextHandle = 1;

  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    const handle = nextHandle;
    nextHandle += 1;
    callbacks.set(handle, callback);
    return handle;
  });
  vi.stubGlobal("cancelAnimationFrame", (handle: number) => {
    callbacks.delete(handle);
  });
  // Arrivals are timed with `performance.now()`; keep it on the same clock.
  vi.spyOn(performance, "now").mockImplementation(() => now);

  return {
    /** Advance one 16ms frame. */
    tick: (steps = 1) => {
      for (let i = 0; i < steps; i += 1) {
        now += 16;
        const scheduled = [...callbacks.values()];
        callbacks.clear();
        act(() => {
          scheduled.forEach((callback) => callback(now));
        });
      }
    },
    pending: () => callbacks.size,
  };
}

describe("useStreamedText", () => {
  let frames: ReturnType<typeof manualFrames>;

  beforeEach(() => {
    frames = manualFrames();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows the initial text immediately", () => {
    const { result } = renderHook(() => useStreamedText("already here"));
    expect(result.current).toBe("already here");
  });

  it("reveals appended text over frames instead of all at once", () => {
    const { result, rerender } = renderHook(
      ({ text }) => useStreamedText(text),
      { initialProps: { text: "Hi" } },
    );

    rerender({ text: `Hi${"x".repeat(200)}` });
    // Not committed on arrival — the clock has not ticked yet.
    expect(result.current).toBe("Hi");

    frames.tick();
    expect(result.current.length).toBeGreaterThan("Hi".length);
    expect(result.current.length).toBeLessThan(202);

    // It still catches up: the backlog drains within a short window.
    frames.tick(40);
    expect(result.current).toBe(`Hi${"x".repeat(200)}`);
    expect(frames.pending()).toBe(0);
  });

  it("reveals bursty chunks at a steady pace once the rate is known", () => {
    const chunk = "x".repeat(40);
    const framesPerChunk = 13;
    const { result, rerender } = renderHook(
      ({ text }) => useStreamedText(text),
      { initialProps: { text: "" } },
    );

    const steps: number[] = [];
    for (let i = 1; i <= 6; i += 1) {
      rerender({ text: chunk.repeat(i) });
      for (let f = 0; f < framesPerChunk; f += 1) {
        const before = result.current.length;
        frames.tick();
        // Skip the first chunks, while the arrival rate is being learned.
        if (i > 3) {
          steps.push(result.current.length - before);
        }
      }
    }

    // Each burst is spread across the gap until the next one rather than
    // revealed up front and followed by a pause.
    expect(Math.max(...steps) - Math.min(...steps)).toBeLessThanOrEqual(2);
    expect(steps.filter((step) => step === 0).length).toBeLessThanOrEqual(1);
  });

  it("catches up on a burst larger than the usual chunk", () => {
    const { result, rerender } = renderHook(
      ({ text }) => useStreamedText(text),
      { initialProps: { text: "" } },
    );
    // Learn a slow rate, then deliver a large burst.
    for (let i = 1; i <= 3; i += 1) {
      rerender({ text: "x".repeat(i * 5) });
      frames.tick(13);
    }
    rerender({ text: "x".repeat(15 + 600) });
    // Drained within roughly the lag cap, not at the slow rate (~2 minutes).
    frames.tick(40);
    expect(result.current.length).toBe(615);
  });

  it("snaps when the text is not an extension of what is shown", () => {
    const { result, rerender } = renderHook(
      ({ text }) => useStreamedText(text),
      { initialProps: { text: "first attempt" } },
    );

    // A higher attempt supersedes the slot; re-typing it would be wrong.
    rerender({ text: "a completely different retry" });
    expect(result.current).toBe("a completely different retry");
  });

  it("cancels the pending frame on unmount", () => {
    const { rerender, unmount } = renderHook(
      ({ text }) => useStreamedText(text),
      { initialProps: { text: "a" } },
    );
    rerender({ text: `a${"b".repeat(50)}` });
    expect(frames.pending()).toBe(1);

    unmount();
    expect(frames.pending()).toBe(0);
  });
});
