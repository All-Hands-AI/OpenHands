import React from "react";
import { cn } from "#/utils/utils";

const SCROLL_EDGE_THRESHOLD_PX = 1;
const FADE_WIDTH_CLASS = "w-10";

export interface ScrollFadeState {
  left: boolean;
  right: boolean;
}

export function readScrollFadeState(element: HTMLDivElement): ScrollFadeState {
  const { scrollLeft, scrollWidth, clientWidth } = element;
  const maxScroll = scrollWidth - clientWidth;
  const hasOverflow = maxScroll > SCROLL_EDGE_THRESHOLD_PX;

  return {
    left: hasOverflow && scrollLeft > SCROLL_EDGE_THRESHOLD_PX,
    right: hasOverflow && scrollLeft < maxScroll - SCROLL_EDGE_THRESHOLD_PX,
  };
}

interface HorizontalScrollFadeProps {
  children: React.ReactNode;
  className?: string;
  scrollClassName?: string;
  scrollTestId?: string;
  fadeTestIdPrefix?: string;
  /**
   * Lets a mouse drag the content sideways and turns a vertical wheel turn
   * into a horizontal scroll while the content overflows. Trackpads and touch
   * scroll natively either way.
   */
  draggable?: boolean;
}

/** Pointer travel beyond which a press counts as a drag, not a click. */
const DRAG_THRESHOLD_PX = 4;

export function HorizontalScrollFade({
  children,
  className,
  scrollClassName,
  scrollTestId,
  fadeTestIdPrefix = "horizontal-scroll-fade",
  draggable = false,
}: HorizontalScrollFadeProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const [fadeState, setFadeState] = React.useState<ScrollFadeState>({
    left: false,
    right: false,
  });

  const updateFadeState = React.useCallback(() => {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    setFadeState(readScrollFadeState(element));
  }, []);

  React.useLayoutEffect(() => {
    updateFadeState();

    const element = scrollRef.current;
    if (!element) {
      return undefined;
    }

    const resizeObserver = new ResizeObserver(updateFadeState);
    resizeObserver.observe(element);

    const content = element.firstElementChild;
    if (content) {
      resizeObserver.observe(content);
    }

    return () => resizeObserver.disconnect();
  }, [updateFadeState, children]);

  React.useEffect(() => {
    const element = scrollRef.current;
    if (!draggable || !element) {
      return undefined;
    }

    let startX = 0;
    let startScrollLeft = 0;
    let isPressed = false;
    let didDrag = false;

    const handlePointerDown = (event: PointerEvent) => {
      if (event.pointerType !== "mouse" || event.button !== 0) return;
      isPressed = true;
      didDrag = false;
      startX = event.clientX;
      startScrollLeft = element.scrollLeft;
    };
    const handlePointerMove = (event: PointerEvent) => {
      if (!isPressed) return;
      const delta = event.clientX - startX;
      if (!didDrag && Math.abs(delta) < DRAG_THRESHOLD_PX) return;
      didDrag = true;
      element.scrollLeft = startScrollLeft - delta;
    };
    const handlePointerEnd = () => {
      isPressed = false;
    };
    // A drag ends on the element it started on; swallow that click so a
    // dragged chip is not also toggled.
    const handleClick = (event: MouseEvent) => {
      if (!didDrag) return;
      didDrag = false;
      event.stopPropagation();
      event.preventDefault();
    };
    const handleWheel = (event: WheelEvent) => {
      if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
      const maxScroll = element.scrollWidth - element.clientWidth;
      if (maxScroll <= SCROLL_EDGE_THRESHOLD_PX) return;
      const next = element.scrollLeft + event.deltaY;
      if (next < 0 || next > maxScroll) return;
      event.preventDefault();
      element.scrollLeft = next;
    };

    element.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerEnd);
    window.addEventListener("pointercancel", handlePointerEnd);
    element.addEventListener("click", handleClick, true);
    element.addEventListener("wheel", handleWheel, { passive: false });
    return () => {
      element.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerEnd);
      window.removeEventListener("pointercancel", handlePointerEnd);
      element.removeEventListener("click", handleClick, true);
      element.removeEventListener("wheel", handleWheel);
    };
  }, [draggable]);

  return (
    <div className={cn("relative max-w-full min-w-0", className)}>
      <div
        ref={scrollRef}
        data-testid={scrollTestId}
        onScroll={updateFadeState}
        className={cn(
          "max-w-full overflow-x-auto scrollbar-hide",
          draggable && "cursor-grab select-none active:cursor-grabbing",
          scrollClassName,
        )}
      >
        {children}
      </div>
      <div
        aria-hidden
        data-testid={`${fadeTestIdPrefix}-left`}
        data-visible={fadeState.left ? "true" : "false"}
        className={cn(
          "pointer-events-none absolute inset-y-0 left-0 z-10",
          FADE_WIDTH_CLASS,
          "bg-gradient-to-r from-[var(--oh-scroll-fade-from,var(--oh-color-base))] to-transparent",
          "transition-opacity duration-300 ease-out motion-reduce:transition-none",
          fadeState.left ? "opacity-100" : "opacity-0",
        )}
      />
      <div
        aria-hidden
        data-testid={`${fadeTestIdPrefix}-right`}
        data-visible={fadeState.right ? "true" : "false"}
        className={cn(
          "pointer-events-none absolute inset-y-0 right-0 z-10",
          FADE_WIDTH_CLASS,
          "bg-gradient-to-l from-[var(--oh-scroll-fade-from,var(--oh-color-base))] to-transparent",
          "transition-opacity duration-300 ease-out motion-reduce:transition-none",
          fadeState.right ? "opacity-100" : "opacity-0",
        )}
      />
    </div>
  );
}
