import { useEffect, useState } from "react";
import React from "react";

type UseElementOverflowParams = {
  contentRef: React.RefObject<HTMLDivElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
};

export function useElementOverflow({
  contentRef,
  containerRef,
}: UseElementOverflowParams): boolean {
  const [isOverflowing, setIsOverflowing] = useState(false);

  useEffect(() => {
    const checkOverflow = () => {
      const container = containerRef.current;
      const content = contentRef.current;
      if (container && content) {
        setIsOverflowing(content.scrollWidth > container.clientWidth);
      }
    };

    checkOverflow();
    const resizeObserver = new ResizeObserver(checkOverflow);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }
    if (contentRef.current) {
      resizeObserver.observe(contentRef.current);
    }

    return () => resizeObserver.disconnect();
  }, [containerRef, contentRef]);

  return isOverflowing;
}
