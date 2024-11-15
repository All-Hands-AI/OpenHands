import { useDispatch, useSelector } from "react-redux";
import React from "react";
import posthog from "posthog-js";
import { useRouteLoaderData } from "@remix-run/react";
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
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import TypingIndicator from "./chat/TypingIndicator";
import ConfirmationButtons from "./chat/ConfirmationButtons";
import { ErrorMessage } from "./error-message";
import { ContinueButton } from "./continue-button";
import { ScrollToBottomButton } from "./scroll-to-bottom-button";
import { Suggestions } from "./suggestions";
import { SUGGESTIONS } from "#/utils/suggestions";
import BuildIt from "#/icons/build-it.svg?react";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import OpenHands from "#/api/open-hands";
import { clientLoader } from "#/routes/_oh";
import { downloadWorkspace } from "#/utils/download-workspace";
import { SuggestionItem } from "./suggestion-item";

const isErrorMessage = (
  message: Message | ErrorMessage,
): message is ErrorMessage => "error" in message;

export function ChatInterface() {
  const { send, status, isLoadingMessages } = useWsClient();

  const dispatch = useDispatch();
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);
  const rootLoaderData = useRouteLoaderData<typeof clientLoader>("routes/_oh");

  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false);
  const [messageToSend, setMessageToSend] = React.useState<string | null>(null);
  const [isDownloading, setIsDownloading] = React.useState(false);

  React.useEffect(() => {
    if (status === WsClientProviderStatus.ACTIVE) {
      try {
        OpenHands.getRuntimeId().then(({ runtime_id }) => {
          // eslint-disable-next-line no-console
          console.log(
            "Runtime ID: %c%s",
            "background: #444; color: #ffeb3b; font-weight: bold; padding: 2px 4px; border-radius: 4px;",
            runtime_id,
          );
        });
      } catch (e) {
        console.warn("Runtime ID not available in this environment");
      }
    }
  }, [status]);

  const handleSendMessage = async (content: string, files: File[]) => {
    posthog.capture("user_message_sent", {
      current_message_count: messages.length,
    });
    const promises = files.map((file) => convertImageToBase64(file));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();
    dispatch(addUserMessage({ content, imageUrls, timestamp }));
    send(createChatMessage(content, imageUrls, timestamp));
    setMessageToSend(null);
  };

  const handleStop = () => {
    posthog.capture("stop_button_clicked");
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

  const handleDownloadWorkspace = async () => {
    setIsDownloading(true);
    try {
      await downloadWorkspace();
    } catch (error) {
      // TODO: Handle error
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="h-full flex flex-col justify-between">
      {messages.length === 0 && (
        <div className="flex flex-col gap-6 h-full px-4 items-center justify-center">
          <div className="flex flex-col items-center p-4 bg-neutral-700 rounded-xl w-full">
            <BuildIt width={45} height={54} />
            <span className="font-semibold text-[20px] leading-6 -tracking-[0.01em] gap-1">
              Let&apos;s start building!
            </span>
          </div>
          <Suggestions
            suggestions={Object.entries(SUGGESTIONS.repo)
              .slice(0, 4)
              .map(([label, value]) => ({
                label,
                value,
              }))}
            onSuggestionClick={(value) => {
              setMessageToSend(value);
            }}
          />
        </div>
      )}

      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4 gap-2"
      >
        {isLoadingMessages && (
          <div className="flex justify-center">
            <div className="w-6 h-6 border-2 border-t-[4px] border-primary-500 rounded-full animate-spin" />
          </div>
        )}

        {!isLoadingMessages &&
          messages.map((message, index) =>
            isErrorMessage(message) ? (
              <ErrorMessage
                key={index}
                id={message.id}
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

        {(curAgentState === AgentState.AWAITING_USER_INPUT ||
          curAgentState === AgentState.FINISHED) && (
          <div className="flex flex-col gap-2 mb-2">
            {rootLoaderData?.ghToken ? (
              <SuggestionItem
                suggestion={{
                  label: "Push to GitHub",
                  value:
                    "Please push the changes to GitHub and open a pull request.",
                }}
                onClick={(value) => {
                  handleSendMessage(value, []);
                }}
              />
            ) : (
              <SuggestionItem
                suggestion={{
                  label: !isDownloading
                    ? "Download .zip"
                    : "Downloading, please wait...",
                  value: "Download .zip",
                }}
                onClick={handleDownloadWorkspace}
              />
            )}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-[6px] px-4 pb-4">
        <div className="flex justify-between relative">
          <FeedbackActions
            onPositiveFeedback={() =>
              onClickShareFeedbackActionButton("positive")
            }
            onNegativeFeedback={() =>
              onClickShareFeedbackActionButton("negative")
            }
          />
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
          value={messageToSend ?? undefined}
          onChange={setMessageToSend}
        />
      </div>

      <FeedbackModal
        isOpen={feedbackModalIsOpen}
        onClose={() => setFeedbackModalIsOpen(false)}
        polarity={feedbackPolarity}
      />
    </div>
  );
}
