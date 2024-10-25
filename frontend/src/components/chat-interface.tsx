import { useDispatch, useSelector } from "react-redux";
import React from "react";
import { useFetcher } from "@remix-run/react";
import { useSocket } from "#/context/socket";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { ChatMessage } from "./chat-message";
import { FeedbackActions } from "./feedback-actions";
import { ImageCarousel } from "./image-carousel";
import { createChatMessage } from "#/services/chatService";
import { InteractiveChatBox } from "./interactive-chat-box";
import { addUserMessage } from "#/state/chatSlice";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { generateAgentStateChangeEvent } from "#/services/agentStateService";
import { FeedbackModal } from "./feedback-modal";
import { Feedback } from "#/api/open-hands.types";
import { getToken } from "#/services/auth";
import { removeApiKey, removeUnwantedKeys } from "#/utils/utils";
import { clientAction } from "#/routes/submit-feedback";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import TypingIndicator from "./chat/TypingIndicator";
import ConfirmationButtons from "./chat/ConfirmationButtons";
import { ErrorMessage } from "./error-message";
import { ContinueButton } from "./continue-button";
import { ScrollToBottomButton } from "./scroll-to-bottom-button";

const FEEDBACK_VERSION = "1.0";

const isErrorMessage = (
  message: Message | ErrorMessage,
): message is ErrorMessage => "error" in message;

export function ChatInterface() {
  const { send, events } = useSocket();
  const dispatch = useDispatch();
  const fetcher = useFetcher<typeof clientAction>({ key: "feedback" });
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackShared, setFeedbackShared] = React.useState(0);
  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false);

  const handleSendMessage = async (content: string, files: File[]) => {
    const promises = files.map((file) => convertImageToBase64(file));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();
    dispatch(addUserMessage({ content, imageUrls, timestamp }));
    send(createChatMessage(content, imageUrls, timestamp));
  };

  const handleStop = () => {
    send(generateAgentStateChangeEvent(AgentState.STOPPED));
  };

  const handleSendContinueMsg = () => {
    handleSendMessage("Continue", []);
  };

  const onClickShareFeedbackActionButton = async (
    polarity: "positive" | "negative",
  ) => {
    setFeedbackModalIsOpen(true);
    setFeedbackPolarity(polarity);
  };

  const handleSubmitFeedback = (
    permissions: "private" | "public",
    email: string,
  ) => {
    const feedback: Feedback = {
      version: FEEDBACK_VERSION,
      feedback: feedbackPolarity,
      email,
      permissions,
      token: getToken(),
      trajectory: removeApiKey(removeUnwantedKeys(events)),
    };

    const formData = new FormData();
    formData.append("feedback", JSON.stringify(feedback));

    fetcher.submit(formData, {
      action: "/submit-feedback",
      method: "POST",
    });

    setFeedbackShared(messages.length);
  };

  return (
    <div className="h-full flex flex-col justify-between">
      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4 gap-2"
      >
        {messages.map((message, index) =>
          isErrorMessage(message) ? (
            <ErrorMessage
              key={index}
              error={message.error}
              message={message.message}
            />
          ) : (
            <ChatMessage
              key={index}
              type={message.sender}
              message={message.content}
            >
              {message.imageUrls.length > 0 && (
                <ImageCarousel size="small" images={message.imageUrls} />
              )}
              {messages.length - 1 === index &&
                message.sender === "assistant" &&
                curAgentState === AgentState.AWAITING_USER_CONFIRMATION && (
                  <ConfirmationButtons />
                )}
            </ChatMessage>
          ),
        )}
      </div>

      <div className="flex flex-col gap-[6px] px-4 pb-4">
        <div className="flex justify-between relative">
          {feedbackShared !== messages.length && messages.length > 3 && (
            <FeedbackActions
              onPositiveFeedback={() =>
                onClickShareFeedbackActionButton("positive")
              }
              onNegativeFeedback={() =>
                onClickShareFeedbackActionButton("negative")
              }
            />
          )}
          <div className="absolute left-1/2 transform -translate-x-1/2 bottom-0">
            {messages.length > 2 &&
              curAgentState === AgentState.AWAITING_USER_INPUT && (
                <ContinueButton onClick={handleSendContinueMsg} />
              )}
            {curAgentState === AgentState.RUNNING && <TypingIndicator />}
          </div>
          {!hitBottom && <ScrollToBottomButton onClick={scrollDomToBottom} />}
        </div>

        <InteractiveChatBox
          onSubmit={handleSendMessage}
          onStop={handleStop}
          isDisabled={
            curAgentState === AgentState.LOADING ||
            curAgentState === AgentState.AWAITING_USER_CONFIRMATION
          }
          mode={curAgentState === AgentState.RUNNING ? "stop" : "submit"}
        />
      </div>

      <FeedbackModal
        isOpen={feedbackModalIsOpen}
        isSubmitting={fetcher.state === "submitting"}
        onClose={() => setFeedbackModalIsOpen(false)}
        onSubmit={handleSubmitFeedback}
      />
    </div>
  );
}
