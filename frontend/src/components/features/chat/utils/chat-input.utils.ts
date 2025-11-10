/**
 * Utility functions for chat input component
 */
/* eslint-disable no-param-reassign */
/**
 * Check if contentEditable element is truly empty
 */
export const isContentEmpty = (element: HTMLDivElement | null): boolean => {
  if (!element) {
    return true;
  }
  const text = element.innerText || element.textContent || "";
  return text.trim() === "";
};

/**
 * Clear empty content from contentEditable element for placeholder display
 */
export const clearEmptyContent = (element: HTMLDivElement | null): void => {
  if (element && isContentEmpty(element)) {
    element.innerHTML = "";
    element.textContent = "";
  }
};

/**
 * Get text content from contentEditable element
 */
export const getTextContent = (element: HTMLDivElement | null): string =>
  element?.innerText || "";

/**
 * Clear text content from contentEditable element
 */
export const clearTextContent = (element: HTMLDivElement | null): void => {
  if (element) {
    element.textContent = "";
  }
};

/**
 * Clear file input value
 */
export const clearFileInput = (element: HTMLInputElement | null): void => {
  if (element) {
    element.value = "";
  }
};

/**
 * Ensure cursor stays visible when content is scrollable
 */
export const ensureCursorVisible = (element: HTMLDivElement | null): void => {
  if (!element) {
    return;
  }

  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    return;
  }

  const range = selection.getRangeAt(0);
  if (!range.getBoundingClientRect || !element.getBoundingClientRect) {
    return;
  }

  const rect = range.getBoundingClientRect();
  const inputRect = element.getBoundingClientRect();

  // If cursor is below the visible area, scroll to show it
  if (rect.bottom > inputRect.bottom) {
    element.scrollTop = element.scrollHeight - element.clientHeight;
  }
};
