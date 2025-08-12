import React, { useRef, useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { ChatSendButton } from "./chat-send-button";
import { ChatAddFileButton } from "./chat-add-file-button";
import { cn } from "#/utils/utils";
import { useAutoResize } from "#/hooks/use-auto-resize";
import { DragOver } from "./drag-over";
import { UploadedFiles } from "./uploaded-files";

export interface CustomChatInputProps {
  disabled?: boolean;
  showButton?: boolean;
  value?: string;
  conversationStatus?: ConversationStatus | null;
  onSubmit: (message: string) => void;
  onStop?: () => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onFilesPaste?: (files: File[]) => void;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
  buttonClassName?: React.HTMLAttributes<HTMLButtonElement>["className"];
}

export function CustomChatInput({
  disabled = false,
  showButton = true,
  value = "",
  conversationStatus = null,
  onSubmit,
  onStop,
  onFocus,
  onBlur,
  onFilesPaste,
  className = "",
  buttonClassName = "",
}: CustomChatInputProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const { t } = useTranslation();

  const chatInputRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Helper function to check if contentEditable is truly empty
  const isContentEmpty = useCallback((): boolean => {
    if (!chatInputRef.current) return true;
    const text =
      chatInputRef.current.innerText || chatInputRef.current.textContent || "";
    return text.trim() === "";
  }, []);

  // Helper function to properly clear contentEditable for placeholder display
  const clearEmptyContent = useCallback((): void => {
    if (chatInputRef.current && isContentEmpty()) {
      chatInputRef.current.innerHTML = "";
      chatInputRef.current.textContent = "";
    }
  }, [isContentEmpty]);

  // Use the auto-resize hook
  const { autoResize } = useAutoResize(chatInputRef, {
    minHeight: 20,
    maxHeight: 80,
    value,
  });

  // Function to add files and notify parent
  const addFiles = useCallback(
    (files: File[]) => {
      // Call onFilesPaste if provided with the new files
      if (onFilesPaste && files.length > 0) {
        onFilesPaste(files);
      }
    },
    [onFilesPaste],
  );

  // File icon click handler
  const handleFileIconClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // File input change handler
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    addFiles(files);
  };

  // Drag and drop event handlers
  const handleDragOver = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    // Only remove drag-over class if we're leaving the container entirely
    if (!chatContainerRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
  };

  // Send button click handler
  const handleSubmit = () => {
    const message = chatInputRef.current?.innerText || "";

    if (message.trim()) {
      onSubmit(message);

      // Clear the input
      if (chatInputRef.current) {
        chatInputRef.current.textContent = "";
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      // Reset height
      autoResize();
    }
  };

  // Resume agent button click handler
  const handleResumeAgent = () => {
    const message = chatInputRef.current?.innerText || "continue";

    onSubmit(message.trim());

    // Clear the input
    if (chatInputRef.current) {
      chatInputRef.current.textContent = "";
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    // Reset height
    autoResize();
  };

  // Handle stop button click
  const handleStop = () => {
    if (onStop) {
      onStop();
    }
  };

  // Handle input events
  const handleInput = () => {
    autoResize();

    // Clear empty content to ensure placeholder shows
    if (chatInputRef.current) {
      clearEmptyContent();
    }

    // Ensure cursor stays visible when content is scrollable
    if (!chatInputRef.current) {
      return;
    }

    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return;
    }

    const range = selection.getRangeAt(0);
    if (
      !range.getBoundingClientRect ||
      !chatInputRef.current.getBoundingClientRect
    ) {
      return;
    }

    const rect = range.getBoundingClientRect();
    const inputRect = chatInputRef.current.getBoundingClientRect();

    // If cursor is below the visible area, scroll to show it
    if (rect.bottom > inputRect.bottom) {
      chatInputRef.current.scrollTop =
        chatInputRef.current.scrollHeight - chatInputRef.current.clientHeight;
    }
  };

  // Handle paste events to clean up formatting
  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();

    // Get plain text from clipboard
    const text = e.clipboardData.getData("text/plain");

    // Insert plain text
    document.execCommand("insertText", false, text);

    // Trigger resize
    setTimeout(autoResize, 0);
  };

  // Handle key events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Send message on Enter (without Shift)
    // Shift+Enter adds a new line (default contenteditable behavior)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
      return;
    }

    // Auto-resize on key events that might change content
    setTimeout(() => {
      autoResize();
      // Ensure cursor stays visible after key navigation
      if (!chatInputRef.current) {
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
        !chatInputRef.current.getBoundingClientRect
      ) {
        return;
      }

      const rect = range.getBoundingClientRect();
      const inputRect = chatInputRef.current.getBoundingClientRect();

      // Scroll to keep cursor visible
      if (rect.top < inputRect.top) {
        chatInputRef.current.scrollTop -= inputRect.top - rect.top + 5;
      } else if (rect.bottom > inputRect.bottom) {
        chatInputRef.current.scrollTop += rect.bottom - inputRect.bottom + 5;
      }
    }, 0);
  };

  // Handle blur events to ensure placeholder shows when empty
  const handleBlur = () => {
    // Clear empty content to ensure placeholder shows
    if (chatInputRef.current) {
      clearEmptyContent();
    }

    // Call the original onBlur callback if provided
    if (onBlur) {
      onBlur();
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        multiple
        accept="*/*"
        style={{ display: "none" }}
        onChange={handleFileInputChange}
        data-testid="upload-image-input"
      />

      {/* Chat Input Component */}
      <div
        ref={chatContainerRef}
        className="bg-[#25272D] box-border content-stretch flex flex-col items-start justify-center p-[16px] relative rounded-[15px] w-full"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Drag Over UI */}
        {isDragOver && <DragOver />}

        <UploadedFiles />

        {/* Main Input Row */}
        <div className="box-border content-stretch flex flex-row items-end justify-between p-0 relative shrink-0 w-full pb-[18px] gap-2">
          <div className="basis-0 box-border content-stretch flex flex-row gap-4 grow items-end justify-start min-h-px min-w-px p-0 relative shrink-0">
            <ChatAddFileButton
              disabled={disabled}
              handleFileIconClick={handleFileIconClick}
            />

            {/* Chat Input Area */}
            <div
              className="box-border content-stretch flex flex-row items-center justify-start min-h-6 p-0 relative shrink-0 flex-1"
              data-name="Text & caret"
            >
              <div className="basis-0 flex flex-col font-normal grow justify-center leading-[0] min-h-px min-w-px overflow-ellipsis overflow-hidden relative shrink-0 text-[#d0d9fa] text-[16px] text-left">
                <div
                  ref={chatInputRef}
                  className={cn(
                    "chat-input bg-transparent text-white text-[16px] font-normal leading-[20px] outline-none resize-none custom-scrollbar min-h-[20px] max-h-[80px] [text-overflow:inherit] [text-wrap-mode:inherit] [white-space-collapse:inherit] block whitespace-pre-wrap",
                    disabled && "cursor-not-allowed",
                  )}
                  contentEditable={!disabled}
                  data-placeholder={t("SUGGESTIONS$WHAT_TO_BUILD")}
                  data-testid="chat-input"
                  onInput={handleInput}
                  onPaste={handlePaste}
                  onKeyDown={handleKeyDown}
                  onFocus={onFocus}
                  onBlur={handleBlur}
                />
              </div>
            </div>
          </div>

          {/* Send Button */}
          {showButton && (
            <ChatSendButton
              buttonClassName={cn(buttonClassName, "translate-y-[3px]")}
              handleSubmit={handleSubmit}
              disabled={disabled}
            />
          )}
        </div>

        <div className="w-full flex items-center justify-between">
          <div className="translate-x-[-6.5px]">
            <ServerStatus conversationStatus={conversationStatus} />
          </div>
          <AgentStatus
            handleStop={handleStop}
            handleResumeAgent={handleResumeAgent}
          />
        </div>
      </div>
    </div>
  );
}
