import { useCallback } from "react";

// Custom hook for cursor management
export const useCursorManagement = (
  inputRef: React.RefObject<HTMLDivElement | null>,
) => {
  const positionCursorAtEnd = useCallback(() => {
    if (!inputRef.current) return;

    const element = inputRef.current;
    const range = document.createRange();
    const selection = window.getSelection();

    if (!selection) return;

    // Find the last text node
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
    );

    let lastTextNode = null;
    let node = walker.nextNode();
    while (node) {
      lastTextNode = node;
      node = walker.nextNode();
    }

    if (lastTextNode) {
      range.setStart(lastTextNode, lastTextNode.textContent?.length || 0);
      range.setEnd(lastTextNode, lastTextNode.textContent?.length || 0);
    } else {
      // If no text nodes, position at the end of the element
      range.selectNodeContents(element);
      range.collapse(false);
    }

    selection.removeAllRanges();
    selection.addRange(range);
  }, [inputRef]);

  const scrollToCursor = useCallback(() => {
    if (!inputRef.current) return;

    const element = inputRef.current;
    const selection = window.getSelection();

    if (!selection || selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    if (!range.getBoundingClientRect) return;

    const rect = range.getBoundingClientRect();
    const elementRect = element.getBoundingClientRect();

    // Calculate if cursor is outside the visible area
    const isCursorBelow = rect.bottom > elementRect.bottom;
    const isCursorAbove = rect.top < elementRect.top;

    if (isCursorBelow) {
      // Scroll down to show cursor
      const scrollAmount = rect.bottom - elementRect.bottom + 10;
      element.scrollTop += scrollAmount;
    } else if (isCursorAbove) {
      // Scroll up to show cursor
      const scrollAmount = elementRect.top - rect.top + 10;
      element.scrollTop -= scrollAmount;
    }
  }, [inputRef]);

  const focusAndPositionCursor = useCallback(() => {
    if (!inputRef.current) return;

    inputRef.current.focus();
    positionCursorAtEnd();
    scrollToCursor();
  }, [inputRef, positionCursorAtEnd, scrollToCursor]);

  return {
    positionCursorAtEnd,
    scrollToCursor,
    focusAndPositionCursor,
  };
};
