import { useSelector, useDispatch } from "react-redux";
import React, { useRef, useCallback, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { ChatSendButton } from "./chat-send-button";
import { ChatAddFileButton } from "./chat-add-file-button";
import { cn } from "#/utils/utils";
import { useAutoResize } from "#/hooks/use-auto-resize";
import { useCursorManagement } from "#/hooks/use-cursor-management";
import ExpandArrowIcon from "#/icons/u-expand-arrows-alt.svg?react";
import CloseIcon from "#/icons/u-close.svg?react";
import { RootState } from "#/store";
import {
  setIsChatInputExpanded,
  setMessageToSend,
} from "#/state/conversation-slice";

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
  const { t } = useTranslation();

  const chatInputRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const chatInputRowRef = useRef<HTMLDivElement>(null);
  const [shouldShowExpandArrow, setShouldShowExpandArrow] = useState(false);
  const [dynamicMaxHeight, setDynamicMaxHeight] = useState(80);

  const isChatInputExpanded = useSelector(
    (state: RootState) => state.conversation.isChatInputExpanded,
  );

  const currentMaxHeight = isChatInputExpanded ? dynamicMaxHeight : 80;

  const dispatch = useDispatch();

  // Function to calculate dynamic max height based on chatInputRowRef height
  const calculateDynamicMaxHeight = useCallback(() => {
    if (!isChatInputExpanded || !chatInputRowRef.current) {
      return 80;
    }

    const rowHeight = chatInputRowRef.current.offsetHeight;
    // Subtract some pixels for padding/margins to ensure proper fit
    const buffer = 24;
    const calculatedHeight = Math.max(rowHeight - buffer, 80); // Minimum 60px

    return calculatedHeight;
  }, [isChatInputExpanded]);

  // Update dynamic max height when expanded state changes
  useEffect(() => {
    if (isChatInputExpanded) {
      // Use setTimeout to ensure the DOM has updated with flex-1 class
      const timer = setTimeout(() => {
        const newMaxHeight = calculateDynamicMaxHeight();
        setDynamicMaxHeight(newMaxHeight);
      }, 0);

      return () => clearTimeout(timer);
    }

    setDynamicMaxHeight(80);
    return undefined;
  }, [isChatInputExpanded, calculateDynamicMaxHeight]);

  // Helper function to check if contentEditable is truly empty
  const isContentEmpty = useCallback((): boolean => {
    if (!chatInputRef.current) return true;
    const text =
      chatInputRef.current.innerText || chatInputRef.current.textContent || "";
    return text.trim() === "";
  }, []);

  // Helper function to update expand arrow visibility
  const updateExpandArrowVisibility = useCallback(() => {
    if (isChatInputExpanded) {
      return;
    }

    const element = chatInputRef.current;
    if (!element) {
      setShouldShowExpandArrow(false);
      return;
    }

    const hasContent = (element.innerText || "").trim() !== "";
    const exceedsMaxHeight = element.scrollHeight > currentMaxHeight;

    setShouldShowExpandArrow(hasContent && exceedsMaxHeight);
  }, [isChatInputExpanded, currentMaxHeight]);

  // Helper function to properly clear contentEditable for placeholder display
  const clearEmptyContent = useCallback((): void => {
    if (chatInputRef.current && isContentEmpty()) {
      chatInputRef.current.innerHTML = "";
      chatInputRef.current.textContent = "";
    }
  }, [isContentEmpty]);

  // Custom hook for cursor management
  const { scrollToCursor, focusAndPositionCursor } =
    useCursorManagement(chatInputRef);

  // Use the auto-resize hook with dynamic maxHeight
  const { autoResize } = useAutoResize(chatInputRef, {
    minHeight: 20,
    maxHeight: currentMaxHeight,
    value,
  });

  // Auto-focus and position cursor when expanded state changes
  useEffect(() => {
    if (!chatInputRef.current || disabled) {
      return undefined;
    }

    // Use setTimeout to ensure DOM has updated
    const timer = setTimeout(() => {
      if (chatInputRef.current) {
        focusAndPositionCursor();
      }
    }, 50); // Small delay to ensure DOM updates are complete

    return () => clearTimeout(timer);
  }, [isChatInputExpanded, disabled, focusAndPositionCursor]);

  // Re-initialize auto-resize when currentMaxHeight changes
  React.useEffect(() => {
    if (chatInputRef.current) {
      autoResize();
    }
  }, [currentMaxHeight, autoResize]);

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
    autoResize();

    // Clear empty content to ensure placeholder shows
    if (chatInputRef.current) {
      clearEmptyContent();
    }

    // Update expand arrow visibility based on current content
    updateExpandArrowVisibility();

    // Ensure cursor stays visible when content is scrollable
    scrollToCursor();
  };

  // Handle paste events to clean up formatting
  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();

    // Get plain text from clipboard
    const text = e.clipboardData.getData("text/plain");

    // Insert plain text
    document.execCommand("insertText", false, text);

    // Trigger resize, update expand arrow, and ensure cursor visibility
    setTimeout(() => {
      autoResize();
      updateExpandArrowVisibility();
      scrollToCursor();
    }, 0);
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
      const isArrowKey = e.key === "ArrowUp" || e.key === "ArrowDown";
      if (isArrowKey) {
        scrollToCursor();
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

  // Check if content exceeds max height and update expand arrow visibility
  useEffect(() => {
    updateExpandArrowVisibility();
  }, [value, updateExpandArrowVisibility]); // Re-run when value prop changes

  const toggleChatInput = (isExpanded: boolean) => {
    dispatch(setMessageToSend(chatInputRef.current?.innerText || ""));
    dispatch(setIsChatInputExpanded(isExpanded));

    // Auto-focus will be handled by the useEffect, but we can also trigger it immediately
    // for better responsiveness when expanding
    if (isExpanded && chatInputRef.current && !disabled) {
      // Use a shorter timeout for immediate response when expanding
      setTimeout(() => {
        if (chatInputRef.current) {
          focusAndPositionCursor();
        }
      }, 10);
    }
  };

  return (
    <div
      className={cn(
        "w-full relative",
        isChatInputExpanded && "h-full",
        className,
      )}
    >
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
        className={cn(
          "bg-[#25272D] box-border content-stretch flex flex-col items-start justify-center p-[16px] relative rounded-[15px] w-full",
          isChatInputExpanded && "h-full justify-end",
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Main Input Row */}
        <div
          ref={chatInputRowRef}
          className={cn(
            "box-border content-stretch flex flex-row items-end justify-between p-0 relative shrink-0 w-full pb-[18px]",
            isChatInputExpanded && "flex-1",
          )}
        >
          <div className="basis-0 box-border content-stretch flex flex-row gap-4 grow items-end justify-start min-h-px min-w-px p-0 relative shrink-0 pt-1">
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
                    `chat-input bg-transparent text-white text-[16px] font-normal leading-[20px] outline-none resize-none custom-scrollbar min-h-[20px] [text-overflow:inherit] [text-wrap-mode:inherit] [white-space-collapse:inherit] block whitespace-pre-wrap`,
                    disabled && "cursor-not-allowed",
                    isChatInputExpanded && `items-start`,
                  )}
                  style={{
                    ...(isChatInputExpanded && {
                      minHeight: `${currentMaxHeight}px`,
                    }),
                    maxHeight: `${currentMaxHeight}px`, // need to use inline style to override the style from the useAutoResize hook.
                  }}
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

      {shouldShowExpandArrow && !isChatInputExpanded && (
        <button
          type="button"
          className={cn(
            "absolute top-5 cursor-pointer",
            isChatInputExpanded ? "right-[24px]" : "right-[26px]",
          )}
          onClick={() => {
            toggleChatInput(true);
          }}
        >
          <ExpandArrowIcon width={15} height={15} color="#9299AA" />
        </button>
      )}

      {isChatInputExpanded && (
        <button
          type="button"
          className={cn(
            "absolute top-5 cursor-pointer",
            isChatInputExpanded ? "right-[24px]" : "right-[26px]",
          )}
          onClick={() => toggleChatInput(false)}
        >
          <CloseIcon width={18} height={18} color="#ffffff" />
        </button>
      )}
    </div>
  );
}
