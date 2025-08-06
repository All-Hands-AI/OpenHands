import { useSelector, useDispatch } from "react-redux";
import React from "react";
import { CustomChatInput } from "./custom-chat-input";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { ImageCarousel } from "../images/image-carousel";
import { FileList } from "../files/file-list";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useChatFileUpload } from "#/hooks/use-chat-file-upload";
import { setDataFromExpandedChatInput } from "#/state/conversation-slice";

export function ExpandedInteractiveChatBox() {
  const dispatch = useDispatch();
  const curAgentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  const messageToSend = useSelector(
    (state: RootState) => state.conversation.messageToSend,
  );

  const isChatInputExpanded = useSelector(
    (state: RootState) => state.conversation.isChatInputExpanded,
  );

  const { data: conversation } = useActiveConversation();

  const {
    images,
    files,
    handleUpload,
    handleRemoveFile,
    handleRemoveImage,
    clearAll,
  } = useChatFileUpload();

  const handleSubmit = (message: string) => {
    // Store data in Redux state for processing by chat interface
    dispatch(
      setDataFromExpandedChatInput({
        message,
        images,
        files,
      }),
    );

    clearAll();
  };

  const handleStop = () => {
    // Default implementation for stopping
    console.log("Stop action triggered");
  };

  const isDisabled =
    curAgentState === AgentState.LOADING ||
    curAgentState === AgentState.AWAITING_USER_CONFIRMATION;

  if (!isChatInputExpanded) {
    return null;
  }

  return (
    <div data-testid="expanded-interactive-chat-box" className="h-full">
      {images.length > 0 && (
        <ImageCarousel
          size="small"
          images={images.map((image) => URL.createObjectURL(image))}
          onRemove={handleRemoveImage}
        />
      )}
      {files.length > 0 && (
        <FileList
          files={files.map((f) => f.name)}
          onRemove={handleRemoveFile}
        />
      )}
      <CustomChatInput
        disabled={isDisabled}
        onSubmit={handleSubmit}
        onStop={handleStop}
        onFilesPaste={handleUpload}
        value={messageToSend ?? undefined}
        conversationStatus={conversation?.status || null}
      />
    </div>
  );
}
