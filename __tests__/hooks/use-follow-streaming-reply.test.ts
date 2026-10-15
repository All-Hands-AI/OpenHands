import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useFollowStreamingReply } from "#/hooks/use-follow-streaming-reply";

/** A scroll container whose geometry the test controls. */
function fakeScroller({ scrollHeight = 1000, clientHeight = 400 } = {}) {
  const element = {
    scrollHeight,
    clientHeight,
    scrollTop: scrollHeight - clientHeight,
  };
  return element as unknown as HTMLElement & typeof element;
}

describe("useFollowStreamingReply", () => {
  let callbacks: Map<number, FrameRequestCallback>;
  const tick = () => {
    const scheduled = [...callbacks.values()];
    callbacks.clear();
    act(() => scheduled.forEach((callback) => callback(0)));
  };

  beforeEach(() => {
    callbacks = new Map();
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
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const setup = (
    element: HTMLElement,
    options: Partial<Parameters<typeof useFollowStreamingReply>[1]> = {},
  ) => {
    const setAutoScroll = vi.fn();
    const props = {
      active: true,
      autoScroll: true,
      setAutoScroll,
      isPaused: () => false,
      ...options,
    };
    const hook = renderHook(
      (p: typeof props) => useFollowStreamingReply({ current: element }, p),
      { initialProps: props },
    );
    return { ...hook, setAutoScroll, props };
  };

  it("keeps the bottom in view as the reply grows", () => {
    const element = fakeScroller();
    setup(element);

    element.scrollHeight = 1100;
    tick();
    expect(element.scrollTop).toBe(700);

    element.scrollHeight = 1180;
    tick();
    expect(element.scrollTop).toBe(780);
  });

  it("stops following as soon as the user scrolls up", () => {
    const element = fakeScroller();
    const { setAutoScroll } = setup(element);
    tick();

    // The user scrolls up before React has re-rendered with autoScroll=false.
    element.scrollTop = 450;
    element.scrollHeight = 1100;
    tick();

    expect(element.scrollTop).toBe(450);
    expect(setAutoScroll).toHaveBeenCalledWith(false);

    element.scrollHeight = 1200;
    tick();
    expect(element.scrollTop).toBe(450);
  });

  it("does not mistake the content shrinking for the user scrolling up", () => {
    const element = fakeScroller();
    const { setAutoScroll } = setup(element);
    tick();

    // The browser clamps scrollTop when the slot is replaced by a shorter
    // finished message; the view is still at the bottom.
    element.scrollHeight = 950;
    element.scrollTop = 550;
    tick();
    element.scrollHeight = 1050;
    tick();

    expect(setAutoScroll).not.toHaveBeenCalled();
    expect(element.scrollTop).toBe(650);
  });

  it("leaves the scroll position alone when the user is not pinned", () => {
    const element = fakeScroller();
    element.scrollTop = 100;
    setup(element, { autoScroll: false });

    element.scrollHeight = 1100;
    tick();
    expect(element.scrollTop).toBe(100);
  });

  it("yields to another scroll adjustment", () => {
    const element = fakeScroller();
    setup(element, { isPaused: () => true });

    element.scrollHeight = 1100;
    tick();
    expect(element.scrollTop).toBe(600);
  });

  it("only runs while a reply is streaming", () => {
    const element = fakeScroller();
    const { rerender, props } = setup(element, { active: false });
    expect(callbacks.size).toBe(0);

    rerender({ ...props, active: true });
    expect(callbacks.size).toBe(1);

    rerender({ ...props, active: false });
    expect(callbacks.size).toBe(0);
  });
});
