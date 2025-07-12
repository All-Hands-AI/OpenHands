import { useCallback, useEffect, useState } from "react";
import React from "react";

const SCROLL_OFFSET = 200;

type UseElementScrollParams = {
  containerRef: React.RefObject<HTMLDivElement | null>;
  scrollRef: React.RefObject<HTMLDivElement | null>;
};

export function useElementScroll({
  containerRef,
  scrollRef,
}: UseElementScrollParams) {
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollState = useCallback(() => {
    const container = containerRef?.current;
    const scroll = scrollRef?.current;
    if (!container || !scroll) {
      return;
    }
    const maxScrollLeft = scroll.scrollWidth - container.clientWidth;

    setCanScrollLeft(scroll.scrollLeft > 0);
    setCanScrollRight(scroll.scrollLeft < maxScrollLeft);
  }, [containerRef, scrollRef]);

  useEffect(() => {
    const scroll = scrollRef?.current;
    if (!scroll) {
      return;
    }
    updateScrollState();

    const preventScroll = (e: Event) => {
      e.preventDefault();
    };
    scroll.addEventListener("wheel", preventScroll, { passive: false });

    scroll.addEventListener("scroll", updateScrollState);
    window.addEventListener("resize", updateScrollState);

    return () => {
      scroll.removeEventListener("wheel", preventScroll);
      scroll.removeEventListener("scroll", updateScrollState);
      window.removeEventListener("resize", updateScrollState);
    };
  }, [updateScrollState]);

  const scrollLeft = useCallback(() => {
    scrollRef?.current?.scrollBy?.({
      left: -SCROLL_OFFSET,
      behavior: "smooth",
    });
  }, []);

  const scrollRight = useCallback(() => {
    scrollRef?.current?.scrollBy?.({ left: SCROLL_OFFSET, behavior: "smooth" });
  }, []);

  return {
    canScrollLeft,
    canScrollRight,
    scrollLeft,
    scrollRight,
  };
}
