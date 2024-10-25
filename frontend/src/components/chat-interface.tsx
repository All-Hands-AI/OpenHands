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
import { cn, removeApiKey, removeUnwantedKeys } from "#/utils/utils";
import { clientAction } from "#/routes/submit-feedback";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import ArrowSendIcon from "#/assets/arrow-send.svg?react";
import ChevronDoubleRight from "#/icons/chevron-double-right.svg?react";
import TypingIndicator from "./chat/TypingIndicator";

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
        className="flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4"
      >
        {messages.map((message, index) =>
          isErrorMessage(message) ? (
            <div key={index} data-testid="error-message">
              <span>{message.error}</span>
              <p>{message.message}</p>
            </div>
          ) : (
            <ChatMessage
              key={index}
              type={message.sender}
              message={message.content}
            >
              {message.imageUrls.length > 0 && (
                <ImageCarousel size="small" images={message.imageUrls} />
              )}
            </ChatMessage>
          ),
        )}
      </div>

      <div className="flex flex-col gap-[6px] px-4 pb-4">
        <div className={cn("flex justify-between relative")}>
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
                <button
                  type="button"
                  onClick={handleSendContinueMsg}
                  className={cn(
                    "px-2 py-1 bg-neutral-700 border border-neutral-600 rounded",
                    "text-[11px] leading-4 tracking-[0.01em] font-[500]",
                    "flex items-center gap-2",
                  )}
                >
                  <ChevronDoubleRight width={12} height={12} />
                  Continue
                </button>
              )}
            {curAgentState === AgentState.RUNNING && <TypingIndicator />}
          </div>
          {!hitBottom && (
            <button
              type="button"
              onClick={scrollDomToBottom}
              data-testid="scroll-to-bottom"
              className="p-1 bg-neutral-700 border border-neutral-600 rounded hover:bg-neutral-500 rotate-180"
            >
              <ArrowSendIcon width={15} height={15} />
            </button>
          )}
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
