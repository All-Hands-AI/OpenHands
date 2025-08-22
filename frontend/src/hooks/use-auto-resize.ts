import { useCallback, useEffect, RefObject } from "react";

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
  value?: string;
  enableManualResize?: boolean;
  onGripDragStart?: () => void;
  onGripDragEnd?: () => void;
}

interface UseAutoResizeReturn {
  autoResize: () => void;
  smartResize: () => void;
  handleGripMouseDown: (e: React.MouseEvent) => void;
}

export const useAutoResize = (
  elementRef: RefObject<HTMLElement | null>,
  options: UseAutoResizeOptions = {},
): UseAutoResizeReturn => {
  const {
    minHeight = 20,
    maxHeight = 120,
    value,
    enableManualResize = false,
    onGripDragStart,
    onGripDragEnd,
  } = options;

  // Auto-resize functionality for contenteditable div
  const autoResize = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    // Reset height to auto to get the actual content height
    element.style.height = "auto";
    element.style.overflowY = "hidden";

    // Set the height based on scroll height, with min and max constraints
    const { scrollHeight } = element;

    if (scrollHeight <= maxHeight) {
      element.style.height = `${Math.max(scrollHeight, minHeight)}px`;
      element.style.overflowY = "hidden";
    } else {
      element.style.height = `${maxHeight}px`;
      element.style.overflowY = "auto";
    }
  }, [elementRef, minHeight, maxHeight]);

  // Smart resize that respects manual height
  const smartResize = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    const currentHeight = element.offsetHeight;
    const currentStyleHeight = parseInt(
      element.style.height || `${minHeight}`,
      10,
    );

    // Temporarily reset to measure content
    element.style.height = "auto";
    const contentHeight = element.scrollHeight;

    // Restore height and determine what to do
    element.style.height = `${currentStyleHeight}px`;

    // If content fits in current height, just manage overflow
    if (contentHeight <= currentHeight) {
      element.style.overflowY = "hidden";
    }
    // If content exceeds current height but is within normal auto-resize range
    else if (contentHeight <= maxHeight) {
      // Only grow if the current height is close to the content height (not manually resized much larger)
      const isManuallyOversized = currentHeight > contentHeight + 50; // 50px threshold
      if (!isManuallyOversized) {
        element.style.height = `${Math.max(contentHeight, minHeight)}px`;
        element.style.overflowY = "hidden";
      } else {
        // Keep manual height but show scrollbar
        element.style.overflowY = "auto";
      }
    }
    // Content exceeds max height
    else {
      element.style.height = `${maxHeight}px`;
      element.style.overflowY = "auto";
    }
  }, [elementRef, minHeight, maxHeight]);

  // Handle mouse down on grip for manual resizing
  const handleGripMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!enableManualResize) return;

      e.preventDefault();

      // Call optional drag start callback
      onGripDragStart?.();

      const startY = e.clientY;
      const startHeight = elementRef.current?.offsetHeight || minHeight;

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const deltaY = moveEvent.clientY - startY;
        // Invert deltaY so moving up increases height and moving down decreases height
        const newHeight = Math.max(
          minHeight,
          Math.min(maxHeight, startHeight - deltaY),
        );

        const element = elementRef.current;
        if (element) {
          element.style.height = `${newHeight}px`;
          element.style.overflowY = newHeight >= maxHeight ? "auto" : "hidden";
        }
      };

      const handleMouseUp = () => {
        // Call optional drag end callback
        onGripDragEnd?.();

        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    },
    [
      elementRef,
      minHeight,
      maxHeight,
      enableManualResize,
      onGripDragStart,
      onGripDragEnd,
    ],
  );

  // Update content and resize when value prop changes
  useEffect(() => {
    const element = elementRef.current;
    if (element && value !== undefined) {
      element.textContent = value;
      autoResize();
    }
  }, [value, autoResize]);

  // Initialize auto-resize on mount
  useEffect(() => {
    autoResize();
  }, [autoResize]);

  return { autoResize, smartResize, handleGripMouseDown };
};
