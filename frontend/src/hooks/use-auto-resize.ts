import { useCallback, useEffect, RefObject } from "react";

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
  value?: string;
  onHeightChange?: (height: number) => void; // New callback for height changes
}

interface UseAutoResizeReturn {
  autoResize: () => void;
}

export const useAutoResize = (
  elementRef: RefObject<HTMLElement | null>,
  options: UseAutoResizeOptions = {},
): UseAutoResizeReturn => {
  const { minHeight = 20, maxHeight = 120, value, onHeightChange } = options;

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

  return { autoResize };
};
