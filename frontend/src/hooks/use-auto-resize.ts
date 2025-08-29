import { useCallback, useEffect, RefObject } from "react";
import { IMessageToSend } from "#/state/conversation-slice";

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
        // Keep manual height but show scrollbar
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

          // Call the height change callback if provided
          if (onHeightChange) {
            onHeightChange(newHeight);
          }
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
      onHeightChange,
    ],
  );

  // Update content and resize when value prop changes
  useEffect(() => {
    const element = elementRef.current;
    if (element && value !== undefined) {
      element.textContent = value.text;
      smartResize();
    }
  }, [value, smartResize]);

  // Initialize auto-resize on mount
  useEffect(() => {
    smartResize();
  }, [smartResize]);

  return { autoResize, smartResize, handleGripMouseDown };
};
