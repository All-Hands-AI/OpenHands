import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import {
  useIsRevealingStreamedText,
  useStreamedText,
} from "#/hooks/use-streamed-text";

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

    // At ~120 chars/s, 200 characters take about 1.7s rather than one burst.
    frames.tick(60);
    expect(result.current.length).toBeLessThan(150);
    frames.tick(50);
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

  it("caps the pace for a fast model but never trails it far", () => {
    const { result, rerender } = renderHook(
      ({ text }) => useStreamedText(text),
      { initialProps: { text: "" } },
    );
    // A model streaming ~600 chars/s, one 10-char chunk per frame.
    let length = 0;
    const stream = (frameCount: number) => {
      for (let f = 0; f < frameCount; f += 1) {
        length += 10;
        rerender({ text: "x".repeat(length) });
        frames.tick();
      }
    };

    stream(62); // ~1s
    // Revealed at a reading pace, not at the model's 600 chars/s.
    expect(result.current.length).toBeLessThan(200);

    stream(560); // ~10s in total
    // Past a few seconds' backlog it speeds up, so it stays within ~5s.
    expect(length - result.current.length).toBeLessThan(600 * 5);
  });

  it("reports while text is still being revealed", () => {
    const revealing = renderHook(() => useIsRevealingStreamedText());
    const { rerender } = renderHook(({ text }) => useStreamedText(text), {
      initialProps: { text: "Hi" },
    });
    expect(revealing.result.current).toBe(false);

    rerender({ text: `Hi${"x".repeat(40)}` });
    expect(revealing.result.current).toBe(true);

    frames.tick(40);
    expect(revealing.result.current).toBe(false);
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
