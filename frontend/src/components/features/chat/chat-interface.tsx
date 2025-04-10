import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { createChatMessage } from "#/services/chat-service";
import { addUserMessage } from "#/state/chat-slice";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import posthog from "posthog-js";
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "react-router";
import { FeedbackModal } from "../feedback/feedback-modal";
import { TrajectoryActions } from "../trajectory/trajectory-actions";
import { ActionSuggestions } from "./action-suggestions";
import { ChatSuggestions } from "./chat-suggestions";
import { InteractiveChatBox } from "./interactive-chat-box";
import { Messages } from "./messages";
import { TypingIndicator } from "./typing-indicator";
import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useGetTrajectory } from "#/hooks/mutation/use-get-trajectory";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { downloadTrajectory } from "#/utils/download-trajectory";

function getEntryPoint(
  hasRepository: boolean | null,
  hasReplayJson: boolean | null,
): string {
  if (hasRepository) return "github";
  if (hasReplayJson) return "replay";
  return "direct";
}

export function ChatInterface() {
  const { send, isLoadingMessages, disconnect, status } = useWsClient();
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  const { messages } = useSelector((state: RootState) => state.chat);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false);
  const [messageToSend, setMessageToSend] = React.useState<string | null>(null);
  const { selectedRepository, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );
  const params = useParams();
  const { mutate: getTrajectory } = useGetTrajectory();

  const handleSendMessage = async (content: string, files: File[]) => {
    if (messages.length === 0) {
      posthog.capture("initial_query_submitted", {
        entry_point: getEntryPoint(
          selectedRepository !== null,
          replayJson !== null,
        ),
        query_character_length: content.length,
        replay_json_size: replayJson?.length,
      });
    } else {
      posthog.capture("user_message_sent", {
        session_message_count: messages.length,
        current_message_length: content.length,
      });
    }
    const promises = files.map((file) => convertImageToBase64(file));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();
    const pending = true;
    dispatch(addUserMessage({ content, imageUrls, timestamp, pending }));
    send(createChatMessage(content, imageUrls, timestamp));
    setMessageToSend(null);
  };

  const handleStop = () => {
    posthog.capture("stop_button_clicked");
    send(generateAgentStateChangeEvent(AgentState.STOPPED));
  };

  const handleDisconnect = () => {
    posthog.capture("websocket_disconnect_clicked");
    disconnect();
  };

  const onClickShareFeedbackActionButton = async (
    polarity: "positive" | "negative",
  ) => {
    setFeedbackModalIsOpen(true);
    setFeedbackPolarity(polarity);
  };

  const onClickExportTrajectoryButton = () => {
    if (!params.conversationId) {
      displayErrorToast(t(I18nKey.CONVERSATION$DOWNLOAD_ERROR));
      return;
    }

    getTrajectory(params.conversationId, {
      onSuccess: async (data) => {
        await downloadTrajectory(
          params.conversationId ?? t(I18nKey.CONVERSATION$UNKNOWN),
          data.trajectory,
        );
      },
      onError: () => {
        displayErrorToast(t(I18nKey.CONVERSATION$DOWNLOAD_ERROR));
      },
    });
  };

  const isWaitingForUserInput =
    curAgentState === AgentState.AWAITING_USER_INPUT ||
    curAgentState === AgentState.FINISHED;

  return (
    <div className="h-full flex flex-col justify-between">
      {messages.length === 0 && (
        <ChatSuggestions onSuggestionsClick={setMessageToSend} />
      )}

      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4 gap-2 fast-smooth-scroll"
      >
        {isLoadingMessages && (
          <div className="flex justify-center">
            <LoadingSpinner size="small" />
          </div>
        )}

        {!isLoadingMessages && (
          <Messages
            messages={messages}
            isAwaitingUserConfirmation={
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION
            }
          />
        )}

        {isWaitingForUserInput && (
          <ActionSuggestions
            onSuggestionsClick={(value) => handleSendMessage(value, [])}
          />
        )}
      </div>

      <div className="flex flex-col gap-[6px] px-4 pb-4">
        <div className="flex justify-between relative">
          <TrajectoryActions
            onPositiveFeedback={() =>
              onClickShareFeedbackActionButton("positive")
            }
            onNegativeFeedback={() =>
              onClickShareFeedbackActionButton("negative")
            }
            onExportTrajectory={() => onClickExportTrajectoryButton()}
          />

          <div className="absolute left-1/2 transform -translate-x-1/2 bottom-0">
            {curAgentState === AgentState.RUNNING && <TypingIndicator />}
          </div>

          {!hitBottom && <ScrollToBottomButton onClick={scrollDomToBottom} />}
        </div>

        <div className="flex items-center gap-2">
          <InteractiveChatBox
            onSubmit={handleSendMessage}
            onStop={handleStop}
            isDisabled={
              curAgentState === AgentState.LOADING ||
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION ||
              status === WsClientProviderStatus.DISCONNECTED
            }
            mode={curAgentState === AgentState.RUNNING ? "stop" : "submit"}
            value={messageToSend ?? undefined}
            onChange={setMessageToSend}
            className="flex-grow w-full pr-1" // Ensure chat box takes full width minus space for the button
          />
          <DisconnectButton
            handleDisconnect={handleDisconnect}
            isDisabled={
              !isWaitingForUserInput &&
              status !== WsClientProviderStatus.DISCONNECTED
            }
          />
        </div>
      </div>

      <FeedbackModal
        isOpen={feedbackModalIsOpen}
        onClose={() => setFeedbackModalIsOpen(false)}
        polarity={feedbackPolarity}
      />
    </div>
  );
}

interface DisconnectButtonProps {
  handleDisconnect: () => void;
  isDisabled: boolean;
}

export function DisconnectButton({
  handleDisconnect,
  isDisabled,
}: DisconnectButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      onClick={handleDisconnect}
      disabled={isDisabled}
      className={`px-3 py-2 rounded-lg font-medium transition-colors ${
        isDisabled
          ? "bg-gray-300 text-gray-500 cursor-not-allowed"
          : "bg-red-500 text-white hover:bg-red-600"
      }`}
    >
      {t(isDisabled ? "Connect" : "Disconnect")}
    </button>
  );
}
