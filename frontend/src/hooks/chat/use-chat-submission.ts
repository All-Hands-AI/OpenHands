import { useCallback } from "react";
import {
  clearTextContent,
  clearFileInput,
} from "#/components/features/chat/utils/chat-input.utils";

/**
 * Hook for handling chat message submission
 */
export const useChatSubmission = (
  chatInputRef: React.RefObject<HTMLDivElement | null>,
  fileInputRef: React.RefObject<HTMLInputElement | null>,
  smartResize: () => void,
  onSubmit: (message: string) => void,
  resetManualResize?: () => void,
) => {
  // Send button click handler
  const handleSubmit = useCallback(() => {
    const message = chatInputRef.current?.innerText || "";
    const trimmedMessage = message.trim();

    if (!trimmedMessage) {
      return;
    }

    // Remove @ symbols before file paths (e.g., @path/to/file.ts -> path/to/file.ts)
    // Only remove @ when preceded by whitespace or at start (not in emails like alona@gmail.com)
    const cleanedMessage = message.replace(/(^|\s)@(\S+)/g, "$1$2");

    onSubmit(cleanedMessage);

    // Clear the input
    clearTextContent(chatInputRef.current);
    clearFileInput(fileInputRef.current);

    // Reset height and show suggestions again
    smartResize();

    // Reset manual resize state for next message
    resetManualResize?.();
  }, [chatInputRef, fileInputRef, smartResize, onSubmit, resetManualResize]);

  // Resume agent button click handler
  const handleResumeAgent = useCallback(() => {
    const message = chatInputRef.current?.innerText || "continue";

    // Remove @ symbols before file paths (e.g., @path/to/file.ts -> path/to/file.ts)
    // Only remove @ when preceded by whitespace or at start (not in emails like alona@gmail.com)
    const cleanedMessage = message.replace(/(^|\s)@(\S+)/g, "$1$2");

    onSubmit(cleanedMessage.trim());

    // Clear the input
    clearTextContent(chatInputRef.current);
    clearFileInput(fileInputRef.current);

    // Reset height and show suggestions again
    smartResize();

    // Reset manual resize state for next message
    resetManualResize?.();
  }, [chatInputRef, fileInputRef, smartResize, onSubmit, resetManualResize]);

  // Handle stop button click
  const handleStop = useCallback((onStop?: () => void) => {
    if (onStop) {
      onStop();
    }
  }, []);

  return {
    handleSubmit,
    handleResumeAgent,
    handleStop,
  };
};
