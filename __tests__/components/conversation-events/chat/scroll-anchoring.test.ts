import { describe, expect, it } from "vitest";
import {
  BOTTOM_THRESHOLD_PX,
  buildInitialMeasurements,
  shouldAdjustScrollOnSizeChange,
} from "#/components/conversation-events/chat/scroll-anchoring";

describe("buildInitialMeasurements", () => {
  it("sizes each row from its measured height plus the inter-row gap", () => {
    const items = buildInitialMeasurements(["a", "b", "c"], [100, 200, 50], 8);

    expect(items.map((item) => item.size)).toEqual([108, 208, 58]);
    expect(items.map((item) => item.start)).toEqual([0, 108, 316]);
    expect(items.map((item) => item.key)).toEqual(["a", "b", "c"]);
    expect(items.at(-1)?.end).toBe(374);
  });

  it("falls back to the measured average for a row whose height was not captured", () => {
    const items = buildInitialMeasurements(["a", "b", "c"], [100, 0, 300], 0);

    // Average of the two captured rows (200) stands in for the missing one, so
    // the seeded total is not dragged down by a zero.
    expect(items.map((item) => item.size)).toEqual([100, 200, 300]);
  });

  it("returns no seed when nothing was measured, leaving the estimate in place", () => {
    expect(buildInitialMeasurements(["a", "b"], [0, 0], 8)).toEqual([]);
    expect(buildInitialMeasurements([], [100], 8)).toEqual([]);
  });
});

describe("shouldAdjustScrollOnSizeChange", () => {
  const makeInstance = (scrollTop: number, clientHeight: number) => {
    const element = {
      scrollTop,
      clientHeight,
      scrollHeight: 1000,
    } as unknown as HTMLElement;
    return { scrollOffset: scrollTop, scrollElement: element };
  };

  it("keeps the default behavior for a row above the viewport", () => {
    const instance = makeInstance(500, 400);

    expect(shouldAdjustScrollOnSizeChange({ start: 100 }, 50, instance)).toBe(
      true,
    );
  });

  it("adjusts when a row below the viewport grows while the reader is pinned to the bottom", () => {
    // Viewport bottom (900) sits at the content bottom (1000) before the row
    // grows by 200; without an adjustment the list would end 200px short.
    const instance = makeInstance(600, 400);

    expect(shouldAdjustScrollOnSizeChange({ start: 800 }, 200, instance)).toBe(
      true,
    );
  });

  it("leaves the offset alone when the reader is not near the bottom", () => {
    const instance = makeInstance(0, 400);

    expect(shouldAdjustScrollOnSizeChange({ start: 800 }, 200, instance)).toBe(
      false,
    );
  });

  it("tolerates a change within the bottom threshold", () => {
    // Bottom is exactly BOTTOM_THRESHOLD_PX short of the pre-change content
    // bottom, which still counts as pinned.
    const element = {
      scrollTop: 600 - BOTTOM_THRESHOLD_PX,
      clientHeight: 400,
      scrollHeight: 1000,
    } as unknown as HTMLElement;
    const instance = {
      scrollOffset: element.scrollTop,
      scrollElement: element,
    };

    expect(shouldAdjustScrollOnSizeChange({ start: 800 }, 100, instance)).toBe(
      true,
    );
  });
});
