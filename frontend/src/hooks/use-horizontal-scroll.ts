import { useRef, useState, useEffect } from "react";

interface UseHorizontalScrollOptions {
  scrollAmount?: number;
  scrollBehavior?: ScrollBehavior;
}

interface UseHorizontalScrollReturn {
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  canScrollLeft: boolean;
  canScrollRight: boolean;
  scroll: (direction: "left" | "right") => void;
  updateScrollArrows: () => void;
}

export function useHorizontalScroll({
  scrollAmount = 200,
  scrollBehavior = "smooth",
}: UseHorizontalScrollOptions = {}): UseHorizontalScrollReturn {
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Check scroll position and update arrow states
  const updateScrollArrows = () => {
    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    // Check if content overflows the container
    const hasOverflow = container.scrollWidth > container.clientWidth;

    if (hasOverflow) {
      // Has overflow - show arrows based on scroll position
      const isAtStart = container.scrollLeft <= 0;
      const isAtEnd =
        container.scrollLeft >=
        container.scrollWidth - container.clientWidth - 1; // -1 for floating point precision

      setCanScrollLeft(!isAtStart);
      setCanScrollRight(!isAtEnd);
      return;
    }

    // No overflow - hide both arrows
    setCanScrollLeft(false);
    setCanScrollRight(false);
  };

  // Get the new scroll left position
  const getNewScrollLeft = (
    container: HTMLDivElement,
    direction: "left" | "right",
  ) => {
    // Incremental scrolling behavior for left direction
    if (direction === "left") {
      return Math.max(0, container.scrollLeft - scrollAmount);
    }

    // For right direction, scroll to the very end of the container
    // Add a small buffer to ensure we reach the true end position
    const maxScrollLeft = container.scrollWidth - container.clientWidth;
    return Math.min(maxScrollLeft, container.scrollLeft + scrollAmount);
  };

  // Calculate scroll amount based on wheel delta
  const calculateWheelScrollAmount = (deltaY: number): number =>
    // Use a smaller multiplier for more controlled scrolling
    Math.min(Math.abs(deltaY) * 0.5, scrollAmount);

  // Determine scroll direction from wheel delta
  const getWheelScrollDirection = (deltaY: number): "left" | "right" =>
    // Map wheel movement to horizontal scrolling:
    // - Scroll down (positive deltaY) → move container right
    // - Scroll up (negative deltaY) → move container left
    deltaY > 0 ? "right" : "left";

  // Calculate new scroll position for wheel scrolling
  const getWheelScrollPosition = (
    container: HTMLDivElement,
    direction: "left" | "right",
    wheelScrollAmount: number,
  ): number => {
    const currentScrollLeft = container.scrollLeft;

    if (direction === "left") {
      return Math.max(0, currentScrollLeft - wheelScrollAmount);
    }

    const maxScrollLeft = container.scrollWidth - container.clientWidth;
    return Math.min(maxScrollLeft, currentScrollLeft + wheelScrollAmount);
  };

  // Scroll left or right
  const scroll = (direction: "left" | "right") => {
    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    const newScrollLeft = getNewScrollLeft(container, direction);

    container.scrollTo({
      left: newScrollLeft,
      behavior: scrollBehavior,
    });

    // Update arrow states after scrolling completes
    updateScrollArrows();
  };

  // Handle mouse wheel scrolling
  const handleWheel = (event: WheelEvent) => {
    event.preventDefault(); // Prevent default vertical scrolling

    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    const { deltaY } = event;
    const direction = getWheelScrollDirection(deltaY);
    const wheelScrollAmount = calculateWheelScrollAmount(deltaY);
    const newScrollLeft = getWheelScrollPosition(
      container,
      direction,
      wheelScrollAmount,
    );

    container.scrollTo({
      left: newScrollLeft,
      behavior: scrollBehavior,
    });

    // Update arrow states after scrolling
    updateScrollArrows();
  };

  // Update scroll arrows on mount and when content changes
  useEffect(() => {
    updateScrollArrows();

    const container = scrollContainerRef.current;
    if (!container) {
      return undefined;
    }

    container.addEventListener("scroll", updateScrollArrows);
    container.addEventListener("wheel", handleWheel, { passive: false });
    window.addEventListener("resize", updateScrollArrows);

    // Use ResizeObserver to detect container size changes
    const resizeObserver = new ResizeObserver(() => {
      updateScrollArrows();
    });
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener("scroll", updateScrollArrows);
      container.removeEventListener("wheel", handleWheel);
      window.removeEventListener("resize", updateScrollArrows);
      resizeObserver.disconnect();
    };
  }, []);

  return {
    scrollContainerRef,
    canScrollLeft,
    canScrollRight,
    scroll,
    updateScrollArrows,
  };
}
