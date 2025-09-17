import React, { useRef, useCallback, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { ConversationStatus } from "#/types/conversation-status";
import { ChatSendButton } from "./chat-send-button";
import { ChatAddFileButton } from "./chat-add-file-button";
import { cn, isMobileDevice } from "#/utils/utils";
import { useAutoResize } from "#/hooks/use-auto-resize";
import { DragOver } from "./drag-over";
import { UploadedFiles } from "./uploaded-files";
import { Tools } from "../controls/tools";
import {
  clearAllFiles,
  setShouldHideSuggestions,
  setSubmittedMessage,
  setMessageToSend,
  setIsRightPanelShown,
} from "#/state/conversation-slice";
import { CHAT_INPUT } from "#/utils/constants";
import { RootState } from "#/store";
import { ServerStatus } from "../controls/server-status";
import { AgentStatus } from "../controls/agent-status";

export interface CustomChatInputProps {
  disabled?: boolean;
  showButton?: boolean;
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
  const [isGripVisible, setIsGripVisible] = useState(false);

  const { messageToSend, submittedMessage, hasRightPanelToggled } = useSelector(
    (state: RootState) => state.conversation,
  );

  const dispatch = useDispatch();

  // Disable input when conversation is stopped
  const isConversationStopped = conversationStatus === "STOPPED";
  const isDisabled = disabled || isConversationStopped;

  // Listen to submittedMessage state changes
  useEffect(() => {
    if (!submittedMessage || disabled) {
      return;
    }
    onSubmit(submittedMessage);
    dispatch(setSubmittedMessage(null));
  }, [submittedMessage, disabled, onSubmit, dispatch]);

  const { t } = useTranslation();

  const chatInputRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const gripRef = useRef<HTMLDivElement>(null);

  // Save current input value when drawer state changes
  useEffect(() => {
    if (chatInputRef.current) {
      const currentText = chatInputRef.current?.innerText || "";
      // Dispatch to save current input value when drawer state changes
      dispatch(setMessageToSend(currentText));
      dispatch(setIsRightPanelShown(hasRightPanelToggled));
    }
  }, [hasRightPanelToggled, dispatch]);

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

  // Drag state management callbacks
  const handleDragStart = useCallback(() => {
    // Keep grip visible during drag by adding a CSS class
    if (gripRef.current) {
      gripRef.current.classList.add("opacity-100");
      gripRef.current.classList.remove("opacity-0");
    }
  }, []);

  const handleDragEnd = useCallback(() => {
    // Restore hover-based visibility
    if (gripRef.current) {
      gripRef.current.classList.remove("opacity-100");
      gripRef.current.classList.add("opacity-0");
    }
  }, []);

  // Handle click on top edge area to toggle grip visibility
  const handleTopEdgeClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsGripVisible((prev) => !prev);
  };

  // Callback to handle height changes and manage suggestions visibility
  const handleHeightChange = useCallback(
    (height: number) => {
      // Hide suggestions when input height exceeds the threshold
      const shouldHideChatSuggestions = height > CHAT_INPUT.HEIGHT_THRESHOLD;
      dispatch(setShouldHideSuggestions(shouldHideChatSuggestions));
    },
    [dispatch],
  );

  // Use the auto-resize hook with height change callback
  const {
    smartResize,
    handleGripMouseDown,
    handleGripTouchStart,
    increaseHeightForEmptyContent,
  } = useAutoResize(chatInputRef, {
    minHeight: 20,
    maxHeight: 400,
    onHeightChange: handleHeightChange,
    onGripDragStart: handleDragStart,
    onGripDragEnd: handleDragEnd,
    value: messageToSend ?? undefined,
    enableManualResize: true,
  });

  // Cleanup: reset suggestions visibility when component unmounts
  useEffect(
    () => () => {
      dispatch(setShouldHideSuggestions(false));
      dispatch(clearAllFiles());
    },
    [dispatch],
  );

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
    if (!isDisabled && fileInputRef.current) {
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
    if (isDisabled) return;
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (isDisabled) return;
    e.preventDefault();
    // Only remove drag-over class if we're leaving the container entirely
    if (!chatContainerRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    if (isDisabled) return;
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

      // Reset height and show suggestions again
      smartResize();
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

    // Reset height and show suggestions again
    smartResize();
  };

  // Handle stop button click
  const handleStop = () => {
    if (onStop) {
      onStop();
    }
  };

  // Handle input events
  const handleInput = () => {
    smartResize();

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
    setTimeout(smartResize, 0);
  };

  // Handle key events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key !== "Enter") {
      return;
    }

    if (isContentEmpty()) {
      e.preventDefault();
      increaseHeightForEmptyContent();
      return;
    }

    // Original submit logic - only for desktop without shift key
    if (!isMobileDevice() && !e.shiftKey && !disabled) {
      e.preventDefault();
      handleSubmit();
    }
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

      {/* Container with grip */}
      <div className="relative w-full">
        {/* Top edge hover area - invisible area that triggers grip visibility */}
        <div
          className="absolute -top-[12px] left-0 w-full h-6 lg:h-3 z-20 group"
          id="resize-grip"
          onClick={handleTopEdgeClick}
        >
          {/* Resize Grip - appears on hover of top edge area, when dragging, or when clicked */}
          <div
            ref={gripRef}
            className={cn(
              "absolute top-[4px] left-0 w-full h-[3px] bg-white cursor-ns-resize z-10 transition-opacity duration-200",
              isGripVisible
                ? "opacity-100"
                : "opacity-0 group-hover:opacity-100",
            )}
            onMouseDown={handleGripMouseDown}
            onTouchStart={handleGripTouchStart}
            style={{ userSelect: "none" }}
          />
        </div>

        {/* Chat Input Component */}
        <div
          ref={chatContainerRef}
          className="bg-[#25272D] box-border content-stretch flex flex-col items-start justify-center p-4 pt-3 relative rounded-[15px] w-full"
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
                    className="chat-input bg-transparent text-white text-[16px] font-normal leading-[20px] outline-none resize-none custom-scrollbar min-h-[20px] max-h-[400px] [text-overflow:inherit] [text-wrap-mode:inherit] [white-space-collapse:inherit] block whitespace-pre-wrap"
                    contentEditable
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
            <div className="flex items-center gap-1">
              <Tools />
              <ServerStatus conversationStatus={conversationStatus} />
            </div>
            <AgentStatus
              handleStop={handleStop}
              handleResumeAgent={handleResumeAgent}
              disabled={disabled}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
