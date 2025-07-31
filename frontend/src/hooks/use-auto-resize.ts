import { useCallback, useEffect, RefObject } from "react";

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
  value?: string;
}

interface UseAutoResizeReturn {
  autoResize: () => void;
  handleInput: () => void;
  handlePaste: (e: React.ClipboardEvent) => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;
}

/* eslint-disable no-param-reassign */
export const useAutoResize = (
  elementRef: RefObject<HTMLDivElement>,
  options: UseAutoResizeOptions = {},
): UseAutoResizeReturn => {
  const { minHeight = 20, maxHeight = 120, value } = options;

  // Auto-resize functionality for contenteditable div
  const autoResize = useCallback(() => {
    if (!elementRef.current) return;

    // Reset height to auto to get the actual content height
    elementRef.current.style.height = "auto";
    elementRef.current.style.overflowY = "hidden";

    // Set the height based on scroll height, with min and max constraints
    const { scrollHeight } = elementRef.current;

    if (scrollHeight <= maxHeight) {
      elementRef.current.style.height = `${Math.max(scrollHeight, minHeight)}px`;
      elementRef.current.style.overflowY = "hidden";
    } else {
      elementRef.current.style.height = `${maxHeight}px`;
      elementRef.current.style.overflowY = "auto";
    }
  }, [elementRef, minHeight, maxHeight]);

  // Helper function to check if contentEditable is truly empty
  const isContentEmpty = useCallback((): boolean => {
    if (!elementRef.current) return true;
    const text =
      elementRef.current.innerText || elementRef.current.textContent || "";
    return text.trim() === "";
  }, [elementRef]);

  // Helper function to properly clear contentEditable for placeholder display
  const clearEmptyContent = useCallback((): void => {
    if (elementRef.current && isContentEmpty()) {
      elementRef.current.innerHTML = "";
      elementRef.current.textContent = "";
    }
  }, [elementRef, isContentEmpty]);

  // Handle input events
  const handleInput = useCallback(() => {
    autoResize();

    // Clear empty content to ensure placeholder shows
    if (elementRef.current) {
      clearEmptyContent();
    }

    // Ensure cursor stays visible when content is scrollable
    if (!elementRef.current) {
      return;
    }

    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return;
    }

    const range = selection.getRangeAt(0);
    if (
      !range.getBoundingClientRect ||
      !elementRef.current.getBoundingClientRect
    ) {
      return;
    }

    const rect = range.getBoundingClientRect();
    const inputRect = elementRef.current.getBoundingClientRect();

    // If cursor is below the visible area, scroll to show it
    if (rect.bottom > inputRect.bottom) {
      elementRef.current.scrollTop =
        elementRef.current.scrollHeight - elementRef.current.clientHeight;
    }
  }, [autoResize, clearEmptyContent, elementRef]);

  // Handle paste events to clean up formatting
  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();

      // Get plain text from clipboard
      const text = e.clipboardData.getData("text/plain");

      // Insert plain text
      document.execCommand("insertText", false, text);

      // Trigger resize
      setTimeout(autoResize, 0);
    },
    [autoResize],
  );

  // Handle key events
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Auto-resize on key events that might change content
      setTimeout(() => {
        autoResize();
        // Ensure cursor stays visible after key navigation
        if (!elementRef.current) {
          return;
        }

        const isArrowKey = e.key === "ArrowUp" || e.key === "ArrowDown";
        if (!isArrowKey) {
          return;
        }

        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
          return;
        }

        const range = selection.getRangeAt(0);
        if (
          !range.getBoundingClientRect ||
          !elementRef.current.getBoundingClientRect
        ) {
          return;
        }

        const rect = range.getBoundingClientRect();
        const inputRect = elementRef.current.getBoundingClientRect();

        // Scroll to keep cursor visible
        if (rect.top < inputRect.top) {
          elementRef.current.scrollTop -= inputRect.top - rect.top + 5;
        } else if (rect.bottom > inputRect.bottom) {
          elementRef.current.scrollTop += rect.bottom - inputRect.bottom + 5;
        }
      }, 0);
    },
    [autoResize, elementRef],
  );

  // Initialize value when prop changes
  useEffect(() => {
    if (elementRef.current && value !== undefined) {
      elementRef.current.textContent = value;
      autoResize();
    }
  }, [value, autoResize, elementRef]);

  // Initialize auto-resize on mount
  useEffect(() => {
    autoResize();
  }, [autoResize]);

  return {
    autoResize,
    handleInput,
    handlePaste,
    handleKeyDown,
  };
};
