import type { VirtualItem } from "@tanstack/react-virtual";

/** Distance from the bottom (px) still treated as "pinned to the bottom". */
export const BOTTOM_THRESHOLD_PX = 20;

/**
 * Seeds the virtualizer's measurement cache from the plain list's own row
 * heights.
 *
 * Crossing the virtualization threshold replaces the plain list (real heights)
 * with the shell (one flat estimate per row). If the estimate's total is
 * shorter than the plain list, the browser clamps `scrollTop` to the new
 * maximum and yanks a reader who was part-way up the history toward the bottom.
 * Seeding every row at the height it just had keeps the shell's total height —
 * and so the scroll offset — unchanged across the switch, and the live
 * measurements then correct any drift in place.
 *
 * Returns `[]` when no heights were captured (or none are usable), which leaves
 * the virtualizer on its own estimate.
 */
export const buildInitialMeasurements = (
  keys: string[],
  heights: number[],
  gapPx: number,
): VirtualItem[] => {
  if (keys.length === 0) return [];
  if (!heights.some((height) => height > 0)) return [];

  // Rows whose height was not captured fall back to the average of the ones
  // that were, so a single unmeasured row cannot distort the total.
  const measured = heights.filter((height) => height > 0);
  const fallback = measured.length
    ? measured.reduce((total, height) => total + height, 0) / measured.length
    : 0;

  let start = 0;
  return keys.map((key, index) => {
    const size = Math.max(1, Math.round(heights[index] || fallback)) + gapPx;
    const item: VirtualItem = {
      index,
      key,
      size,
      lane: 0,
      start,
      end: start + size,
    };
    start += size;
    return item;
  });
};

interface SizeChangeInstance {
  scrollOffset: number | null;
  scrollElement: Element | null;
}

/**
 * Decides whether a row's height correction should move the scroll offset.
 *
 * The virtualizer's default keeps the *content* under the viewport fixed when a
 * row above it is measured (`item.start < scrollOffset`). The case it misses is
 * a tall row at or below the viewport growing while the reader is pinned to the
 * bottom: nothing shifts the offset, so the list ends up short of the bottom
 * and "scroll to bottom" appears to have stopped early. Detecting that case
 * needs the height *before* the change, which is `scrollHeight - delta`.
 */
export const shouldAdjustScrollOnSizeChange = (
  item: Pick<VirtualItem, "start">,
  delta: number,
  instance: SizeChangeInstance,
): boolean => {
  const offset = instance.scrollOffset ?? 0;
  if (item.start < offset) return true;

  const element = instance.scrollElement as HTMLElement | null;
  if (!element || delta === 0) return false;

  const heightBefore = element.scrollHeight - delta;
  return (
    element.scrollTop + element.clientHeight >=
    heightBefore - BOTTOM_THRESHOLD_PX
  );
};
