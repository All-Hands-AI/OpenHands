import React, { useRef, useCallback } from "react";
import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { ChatSendButton } from "./chat-send-button";
import { ChatAddFileButton } from "./chat-add-file-button";
import { cn } from "#/utils/utils";
import { useAutoResize } from "#/hooks/use-auto-resize";

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
  const chatInputRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Use the auto-resize custom hook
  const {
    autoResize,
    handleInput: handleAutoResizeInput,
    handlePaste: handleAutoResizePaste,
    handleKeyDown: handleAutoResizeKeyDown,
  } = useAutoResize(chatInputRef as React.RefObject<HTMLDivElement>, { value });

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
    handleAutoResizeInput();
  };

  // Handle paste events to clean up formatting
  const handlePaste = (e: React.ClipboardEvent) => {
    handleAutoResizePaste(e);
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

    // Use the auto-resize hook's key down handler
    handleAutoResizeKeyDown(e);
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
        {/* Main Input Row */}
        <div className="box-border content-stretch flex flex-row items-center justify-between p-0 relative shrink-0 w-full pb-[18px]">
          <div className="basis-0 box-border content-stretch flex flex-row gap-4 grow items-center justify-start min-h-px min-w-px p-0 relative shrink-0">
            <ChatAddFileButton
              disabled={disabled}
              handleFileIconClick={handleFileIconClick}
            />

            {/* Chat Input Area */}
            <div
              className="box-border content-stretch flex flex-row items-center justify-start min-h-6 p-0 relative shrink-0 flex-1"
              data-name="Text & caret"
            >
              <div className="basis-0 flex flex-col font-['Outfit:Regular',_sans-serif] font-normal grow justify-center leading-[0] min-h-px min-w-px overflow-ellipsis overflow-hidden relative shrink-0 text-[#d0d9fa] text-[16px] text-left">
                <div
                  ref={chatInputRef}
                  className={cn(
                    "chat-input bg-transparent text-white text-[16px] font-normal leading-[20px] outline-none resize-none custom-scrollbar min-h-[20px] max-h-[120px] [text-overflow:inherit] [text-wrap-mode:inherit] [white-space-collapse:inherit] block whitespace-pre-wrap",
                    disabled && "cursor-not-allowed",
                  )}
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
          <AgentStatus
            handleStop={handleStop}
            handleResumeAgent={handleResumeAgent}
          />
        </div>
      </div>
    </div>
  );
}
