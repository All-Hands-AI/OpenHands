import React, { useRef, useEffect, useCallback } from "react";
import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { ChatSendButton } from "./chat-send-button";
import { ChatAddFileButton } from "./chat-add-file-button";
import { ChatStopButton } from "./chat-stop-button";

export interface CustomChatInputProps {
  disabled?: boolean;
  button?: "submit" | "stop";
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
  button = "submit",
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

  // Auto-resize functionality for contenteditable div
  const autoResize = useCallback(() => {
    if (!chatInputRef.current) return;

    // Reset height to auto to get the actual content height
    chatInputRef.current.style.height = "auto";
    chatInputRef.current.style.overflowY = "hidden";

    // Set the height based on scroll height, with min and max constraints
    const { scrollHeight } = chatInputRef.current;
    const minHeight = 20; // minimum height in px
    const maxHeight = 120; // maximum height in px

    if (scrollHeight <= maxHeight) {
      chatInputRef.current.style.height = `${Math.max(scrollHeight, minHeight)}px`;
      chatInputRef.current.style.overflowY = "hidden";
    } else {
      chatInputRef.current.style.height = `${maxHeight}px`;
      chatInputRef.current.style.overflowY = "auto";
    }
  }, []);

  useEffect(() => {
    if (chatInputRef.current && value !== undefined) {
      chatInputRef.current.textContent = value;
      autoResize();
    }
  }, [value, autoResize]);

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
    chatContainerRef.current?.classList.add("drag-over");
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    // Only remove drag-over class if we're leaving the container entirely
    if (!chatContainerRef.current?.contains(e.relatedTarget as Node)) {
      chatContainerRef.current?.classList.remove("drag-over");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    chatContainerRef.current?.classList.remove("drag-over");

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

  // Initialize value when prop changes
  useEffect(() => {
    if (chatInputRef.current && value !== undefined) {
      chatInputRef.current.textContent = value;
      autoResize();
    }
  }, [value, autoResize]);

  // Initialize auto-resize on mount
  useEffect(() => {
    autoResize();
  }, [autoResize]);

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
        className="bg-[rgba(208,217,250,0.15)] box-border content-stretch flex flex-col items-start justify-center p-[16px] relative rounded-[15px] w-full"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Main Input Row */}
        <div className="box-border content-stretch flex flex-row items-center justify-between p-0 relative shrink-0 w-full pb-[18px]">
          <div className="basis-0 box-border content-stretch flex flex-row gap-4 grow items-center justify-start min-h-px min-w-px p-0 relative shrink-0">
            <ChatAddFileButton handleFileIconClick={handleFileIconClick} />

            {/* Chat Input Area */}
            <div
              className="box-border content-stretch flex flex-row items-center justify-start min-h-6 p-0 relative shrink-0 flex-1"
              data-name="Text & caret"
            >
              <div className="basis-0 flex flex-col font-['Outfit:Regular',_sans-serif] font-normal grow justify-center leading-[0] min-h-px min-w-px overflow-ellipsis overflow-hidden relative shrink-0 text-[#d0d9fa] text-[16px] text-left">
                <div
                  ref={chatInputRef}
                  className="chat-input bg-transparent text-[#d0d9fa] text-[16px] font-normal leading-[20px] outline-none resize-none custom-scrollbar min-h-[20px] max-h-[120px] [text-overflow:inherit] [text-wrap-mode:inherit] [white-space-collapse:inherit] block whitespace-pre-wrap"
                  contentEditable={!disabled}
                  data-placeholder="What do you want to build?"
                  data-testid="chat-input"
                  style={{ fontFamily: "'Outfit', sans-serif" }}
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
              buttonClassName={buttonClassName}
              handleSubmit={handleSubmit}
              disabled={disabled}
            />
          )}
        </div>

        <div className="w-full flex items-center justify-between">
          <ServerStatus conversationStatus={conversationStatus} />
          <div className="flex items-center gap-1">
            <AgentStatus />
            {button === "stop" && <ChatStopButton handleStop={handleStop} />}
          </div>
        </div>
      </div>
    </div>
  );
}
