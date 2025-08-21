import { useCallback, useEffect, RefObject } from "react";
import { IMessageToSend } from "#/state/conversation-slice";

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
  value?: IMessageToSend;
}

interface UseAutoResizeReturn {
  autoResize: () => void;
}

export const useAutoResize = (
  elementRef: RefObject<HTMLElement | null>,
  options: UseAutoResizeOptions = {},
): UseAutoResizeReturn => {
  const { minHeight = 20, maxHeight = 120, value } = options;

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

  // Update content and resize when value prop changes
  useEffect(() => {
    const element = elementRef.current;
    if (element && value !== undefined) {
      element.textContent = value.text;
      autoResize();
    }
  }, [value, autoResize]);

  // Initialize auto-resize on mount
  useEffect(() => {
    autoResize();
  }, [autoResize]);

  return { autoResize };
};
