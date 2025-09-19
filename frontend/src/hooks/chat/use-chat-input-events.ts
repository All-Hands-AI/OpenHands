import { useCallback } from "react";
import { isMobileDevice } from "#/utils/utils";
import {
  ensureCursorVisible,
  clearEmptyContent,
} from "#/components/features/chat/utils/chat-input.utils";

/**
 * Hook for handling chat input events
 */
export const useChatInputEvents = (
  chatInputRef: React.RefObject<HTMLDivElement | null>,
  smartResize: () => void,
  increaseHeightForEmptyContent: () => void,
  checkIsContentEmpty: () => boolean,
  clearEmptyContentHandler: () => void,
  onFocus?: () => void,
  onBlur?: () => void,
) => {
  // Handle input events
  const handleInput = useCallback(() => {
    smartResize();

    // Clear empty content to ensure placeholder shows
    if (chatInputRef.current) {
      clearEmptyContent(chatInputRef.current);
    }

    // Ensure cursor stays visible when content is scrollable
    ensureCursorVisible(chatInputRef.current);
  }, [smartResize, chatInputRef]);

  // Handle paste events to clean up formatting
  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();

      // Get plain text from clipboard
      const text = e.clipboardData.getData("text/plain");

      // Insert plain text
      document.execCommand("insertText", false, text);

      // Trigger resize
      setTimeout(smartResize, 0);
    },
    [smartResize],
  );

  // Handle key events
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, disabled: boolean, handleSubmit: () => void) => {
      if (e.key !== "Enter") {
        return;
      }

      if (checkIsContentEmpty()) {
        e.preventDefault();
        increaseHeightForEmptyContent();
        return;
      }

      // Original submit logic - only for desktop without shift key
      if (!isMobileDevice() && !e.shiftKey && !disabled) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [checkIsContentEmpty, increaseHeightForEmptyContent],
  );

  // Handle blur events to ensure placeholder shows when empty
  const handleBlur = useCallback(() => {
    // Clear empty content to ensure placeholder shows
    if (chatInputRef.current) {
      clearEmptyContent(chatInputRef.current);
    }

    // Call the original onBlur callback if provided
    if (onBlur) {
      onBlur();
    }
  }, [chatInputRef, onBlur]);

  // Handle focus events
  const handleFocus = useCallback(() => {
    if (onFocus) {
      onFocus();
    }
  }, [onFocus]);

  return {
    handleInput,
    handlePaste,
    handleKeyDown,
    handleBlur,
    handleFocus,
  };
};
