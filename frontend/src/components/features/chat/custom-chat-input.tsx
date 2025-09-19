import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { ConversationStatus } from "#/types/conversation-status";
import {
  clearAllFiles,
  setShouldHideSuggestions,
  setSubmittedMessage,
} from "#/state/conversation-slice";
import { RootState } from "#/store";
import { useChatInputLogic } from "#/hooks/chat/use-chat-input-logic";
import { useFileHandling } from "#/hooks/chat/use-file-handling";
import { useGripResize } from "#/hooks/chat/use-grip-resize";
import { useChatInputEvents } from "#/hooks/chat/use-chat-input-events";
import { useChatSubmission } from "#/hooks/chat/use-chat-submission";
import { ChatInputGrip } from "./components/chat-input-grip";
import { ChatInputContainer } from "./components/chat-input-container";
import { HiddenFileInput } from "./components/hidden-file-input";

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
  const { submittedMessage } = useSelector(
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

  // Custom hooks
  const {
    chatInputRef,
    messageToSend,
    checkIsContentEmpty,
    clearEmptyContentHandler,
  } = useChatInputLogic();

  const {
    fileInputRef,
    chatContainerRef,
    isDragOver,
    handleFileIconClick,
    handleFileInputChange,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  } = useFileHandling(onFilesPaste);

  const {
    gripRef,
    isGripVisible,
    handleTopEdgeClick,
    smartResize,
    handleGripMouseDown,
    handleGripTouchStart,
    increaseHeightForEmptyContent,
  } = useGripResize(
    chatInputRef as React.RefObject<HTMLDivElement | null>,
    messageToSend,
  );

  const { handleSubmit, handleResumeAgent, handleStop } = useChatSubmission(
    chatInputRef as React.RefObject<HTMLDivElement | null>,
    fileInputRef as React.RefObject<HTMLInputElement | null>,
    smartResize,
    onSubmit,
  );

  const { handleInput, handlePaste, handleKeyDown, handleBlur, handleFocus } =
    useChatInputEvents(
      chatInputRef as React.RefObject<HTMLDivElement | null>,
      smartResize,
      increaseHeightForEmptyContent,
      checkIsContentEmpty,
      clearEmptyContentHandler,
      onFocus,
      onBlur,
    );

  // Cleanup: reset suggestions visibility when component unmounts
  useEffect(
    () => () => {
      dispatch(setShouldHideSuggestions(false));
      dispatch(clearAllFiles());
    },
    [dispatch],
  );

  return (
    <div className={`w-full ${className}`}>
      {/* Hidden file input */}
      <HiddenFileInput
        fileInputRef={fileInputRef}
        onChange={handleFileInputChange}
      />

      {/* Container with grip */}
      <div className="relative w-full">
        <ChatInputGrip
          gripRef={gripRef}
          isGripVisible={isGripVisible}
          handleTopEdgeClick={handleTopEdgeClick}
          handleGripMouseDown={handleGripMouseDown}
          handleGripTouchStart={handleGripTouchStart}
        />

        <ChatInputContainer
          chatContainerRef={chatContainerRef}
          isDragOver={isDragOver}
          disabled={isDisabled}
          showButton={showButton}
          buttonClassName={buttonClassName}
          conversationStatus={conversationStatus}
          chatInputRef={chatInputRef}
          handleFileIconClick={handleFileIconClick}
          handleSubmit={handleSubmit}
          handleStop={handleStop}
          handleResumeAgent={handleResumeAgent}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onInput={handleInput}
          onPaste={handlePaste}
          onKeyDown={(e) => handleKeyDown(e, isDisabled, handleSubmit)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onStop={onStop}
        />
      </div>
    </div>
  );
}
