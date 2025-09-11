import { useCallback, useEffect, RefObject } from "react";
import { IMessageToSend } from "#/state/conversation-slice";
import { isMobileDevice } from "#/utils/utils";

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
  enableManualResize?: boolean;
  onGripDragStart?: () => void;
  onGripDragEnd?: () => void;
  onHeightChange?: (height: number) => void; // New callback for height changes
  value?: IMessageToSend;
}

interface UseAutoResizeReturn {
  autoResize: () => void;
  smartResize: () => void;
  handleGripMouseDown: (e: React.MouseEvent) => void;
  handleGripTouchStart: (e: React.TouchEvent) => void;
  increaseHeightForEmptyContent: () => void;
}

export const useAutoResize = (
  elementRef: RefObject<HTMLElement | null>,
  options: UseAutoResizeOptions = {},
): UseAutoResizeReturn => {
  const {
    minHeight = 20,
    maxHeight = 120,
    enableManualResize = false,
    value,
    onGripDragStart,
    onGripDragEnd,
    onHeightChange,
  } = options;

  // Helper function to calculate final height and apply styles
  const calculateAndApplyHeight = useCallback(
    (element: HTMLElement, scrollHeight: number) => {
      let finalHeight: number;

      if (scrollHeight <= maxHeight) {
        finalHeight = Math.max(scrollHeight, minHeight);
        element.style.setProperty("height", `${finalHeight}px`);
        element.style.setProperty("overflow-y", "hidden");
      } else {
        finalHeight = maxHeight;
        element.style.setProperty("height", `${maxHeight}px`);
        element.style.setProperty("overflow-y", "auto");
      }

      return finalHeight;
    },
    [minHeight, maxHeight],
  );

  // Auto-resize functionality for contenteditable div
  const autoResize = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    // Reset height to auto to get the actual content height
    element.style.setProperty("height", "auto");
    element.style.setProperty("overflow-y", "hidden");

    // Set the height based on scroll height, with min and max constraints
    const { scrollHeight } = element;
    const finalHeight = calculateAndApplyHeight(element, scrollHeight);

    // Call the height change callback if provided
    if (onHeightChange) {
      onHeightChange(finalHeight);
    }
  }, [elementRef, calculateAndApplyHeight, onHeightChange]);

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

    let finalHeight = currentHeight;

    // If content fits in current height, just manage overflow
    if (contentHeight <= currentHeight) {
      element.style.overflowY = "hidden";
      finalHeight = currentHeight;
    }
    // If content exceeds current height but is within normal auto-resize range
    else if (contentHeight <= maxHeight) {
      // Only grow if the current height is close to the content height (not manually resized much larger)
      const isManuallyOversized = currentHeight > contentHeight + 50; // 50px threshold
      if (!isManuallyOversized) {
        finalHeight = Math.max(contentHeight, minHeight);
        element.style.height = `${finalHeight}px`;
        element.style.overflowY = "hidden";
      } else {
        // Keep manual height but show scrollbar since content exceeds visible area
        element.style.overflowY = "auto";
        finalHeight = currentHeight;
      }
    }
    // Content exceeds max height
    else {
      finalHeight = maxHeight;
      element.style.height = `${maxHeight}px`;
      element.style.overflowY = "auto";
    }

    // Call the height change callback if provided
    if (onHeightChange) {
      onHeightChange(finalHeight);
    }
  }, [elementRef, minHeight, maxHeight, onHeightChange]);

  // Helper function to extract Y coordinate from mouse or touch events
  const getClientY = useCallback((event: MouseEvent | TouchEvent): number => {
    if ("touches" in event && event.touches.length > 0) {
      return event.touches[0].clientY;
    }
    return (event as MouseEvent).clientY;
  }, []);

  // Core drag logic shared between mouse and touch events
  const createDragHandlers = useCallback(
    (startY: number, startHeight: number, isMobile: boolean) => {
      const handleMove = (moveEvent: MouseEvent | TouchEvent) => {
        moveEvent.preventDefault();

        const deltaY = getClientY(moveEvent) - startY;
        // Invert deltaY so moving up increases height and moving down decreases height
        const newHeight = Math.max(
          minHeight,
          Math.min(maxHeight, startHeight - deltaY),
        );

        const element = elementRef.current;
        if (element) {
          element.style.height = `${newHeight}px`;

          // Check if content exceeds the new height to determine scrollbar visibility
          const contentHeight = element.scrollHeight;
          const shouldShowScrollbar =
            contentHeight > newHeight || newHeight >= maxHeight;
          element.style.overflowY = shouldShowScrollbar ? "auto" : "hidden";

          // Call the height change callback if provided
          if (onHeightChange) {
            onHeightChange(newHeight);
          }
        }
      };

      const handleEnd = () => {
        // Call optional drag end callback
        onGripDragEnd?.();

        if (isMobile) {
          const resizeGrip = document.getElementById("resize-grip");
          if (!resizeGrip) return;

          // Remove both mouse and touch event listeners
          resizeGrip.removeEventListener("mousemove", handleMove);
          resizeGrip.removeEventListener("mouseup", handleEnd);
          resizeGrip.removeEventListener("touchmove", handleMove);
          resizeGrip.removeEventListener("touchend", handleEnd);
        } else {
          document.removeEventListener("mousemove", handleMove);
          document.removeEventListener("mouseup", handleEnd);
          document.removeEventListener("touchmove", handleMove);
          document.removeEventListener("touchend", handleEnd);
        }
      };

      return { handleMove, handleEnd };
    },
    [
      elementRef,
      minHeight,
      maxHeight,
      onGripDragEnd,
      onHeightChange,
      getClientY,
    ],
  );

  // Common drag start logic shared between mouse and touch events
  const startDrag = useCallback(
    (startY: number) => {
      if (!enableManualResize) {
        return;
      }

      // Call optional drag start callback
      onGripDragStart?.();

      const isMobile = isMobileDevice();

      const startHeight = elementRef.current?.offsetHeight || minHeight;
      const { handleMove, handleEnd } = createDragHandlers(
        startY,
        startHeight,
        isMobile,
      );

      if (isMobile) {
        const resizeGrip = document.getElementById("resize-grip");
        if (!resizeGrip) {
          return;
        }
        resizeGrip.addEventListener("touchmove", handleMove, {
          passive: false,
          capture: true,
        });
        resizeGrip.addEventListener("touchend", handleEnd, { capture: true });
      } else {
        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", handleEnd);
      }
    },
    [
      elementRef,
      minHeight,
      enableManualResize,
      onGripDragStart,
      createDragHandlers,
    ],
  );

  // Handle mouse down on grip for manual resizing
  const handleGripMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      startDrag(e.clientY);
    },
    [startDrag],
  );

  // Handle touch start on grip for manual resizing
  const handleGripTouchStart = useCallback(
    (e: React.TouchEvent) => {
      e.preventDefault();
      startDrag(e.touches[0].clientY);
    },
    [startDrag],
  );

  // Update content and resize when value prop changes
  useEffect(() => {
    const element = elementRef.current;
    if (element && value !== undefined) {
      element.textContent = value.text;
      smartResize();
    }
  }, [value, smartResize]);

  // Function to increase height by 20px when content is empty
  const increaseHeightForEmptyContent = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    const currentHeight = element.offsetHeight;
    const newHeight = Math.min(currentHeight + 20, maxHeight);

    if (newHeight > currentHeight) {
      element.style.setProperty("height", `${newHeight}px`);
      element.style.setProperty(
        "overflow-y",
        newHeight >= maxHeight ? "auto" : "hidden",
      );

      // Call the height change callback if provided
      if (onHeightChange) {
        onHeightChange(newHeight);
      }
    }
  }, [elementRef, maxHeight, onHeightChange]);

  // Initialize auto-resize on mount
  useEffect(() => {
    smartResize();
  }, [smartResize]);

  return {
    autoResize,
    smartResize,
    handleGripMouseDown,
    handleGripTouchStart,
    increaseHeightForEmptyContent,
  };
};
