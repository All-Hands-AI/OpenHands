import { useSelector } from "react-redux";
import React from "react";
import posthog from "posthog-js";
import { useParams } from "react-router";
import { useTranslation } from "react-i18next";
import hotToast from "react-hot-toast";
import { I18nKey } from "#/i18n/declaration";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { TrajectoryActions } from "../trajectory/trajectory-actions";
import { createChatMessage, createUserFeedback } from "#/services/chat-service";
import { InteractiveChatBox } from "./interactive-chat-box";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { TypingIndicator } from "./typing-indicator";
import { useWsClient } from "#/context/ws-client-provider";
import { Messages } from "./messages";
import { ChatSuggestions } from "./chat-suggestions";
import { ActionSuggestions } from "./action-suggestions";
import { FeedbackModal } from "../feedback/feedback-modal";

import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useGetTrajectory } from "#/hooks/mutation/use-get-trajectory";
import { downloadTrajectory } from "#/utils/download-trajectory";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { useWSErrorMessage } from "#/hooks/use-ws-error-message";
import { ErrorMessageBanner } from "./error-message-banner";
import { shouldRenderEvent } from "./event-content-helpers/should-render-event";

function getEntryPoint(
  hasRepository: boolean | null,
  hasReplayJson: boolean | null,
): string {
  if (hasRepository) return "github";
  if (hasReplayJson) return "replay";
  return "direct";
}

export function ChatInterface() {
  const { getErrorMessage } = useWSErrorMessage();
  const { send, isLoadingMessages, parsedEvents } = useWsClient();
  const { setOptimisticUserMessage, getOptimisticUserMessage } =
    useOptimisticUserMessage();
  const { t } = useTranslation();
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef);

  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false);
  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [messageToSend, setMessageToSend] = React.useState<string | null>(null);
  const { selectedRepository, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );
  const params = useParams();
  const { mutate: getTrajectory } = useGetTrajectory();

  const optimisticUserMessage = getOptimisticUserMessage();
  const errorMessage = getErrorMessage();

  const events = parsedEvents.filter(shouldRenderEvent);

  const handleSendMessage = async (content: string, files: File[]) => {
    if (events.length === 0) {
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
        session_message_count: events.length,
        current_message_length: content.length,
      });
    }
    const promises = files.map((file) => convertImageToBase64(file));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();
    send(createChatMessage(content, imageUrls, timestamp));
    setOptimisticUserMessage(content);
    setMessageToSend(null);
  };

  const handleStop = () => {
    posthog.capture("stop_button_clicked");
    send(generateAgentStateChangeEvent(AgentState.STOPPED));
  };

  const onClickShareFeedbackActionButton = (
    polarity: "positive" | "negative",
  ) => {
    // Open the feedback modal with the selected polarity
    setFeedbackPolarity(polarity);
    setFeedbackModalIsOpen(true);

    // Track the feedback button click
    posthog.capture("feedback_button_clicked", {
      polarity,
    });
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
      {events.length === 0 && !optimisticUserMessage && (
        <ChatSuggestions onSuggestionsClick={setMessageToSend} />
      )}

      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="scrollbar scrollbar-thin scrollbar-thumb-gray-400 scrollbar-thumb-rounded-full scrollbar-track-gray-800 hover:scrollbar-thumb-gray-300 flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4 gap-2 fast-smooth-scroll"
      >
        {isLoadingMessages && (
          <div className="flex justify-center">
            <LoadingSpinner size="small" />
          </div>
        )}

        {!isLoadingMessages && (
          <Messages
            messages={events}
            isAwaitingUserConfirmation={
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION
            }
          />
        )}

        {isWaitingForUserInput &&
          events.length > 0 &&
          !optimisticUserMessage && (
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

        {errorMessage && <ErrorMessageBanner message={errorMessage} />}

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
        onClose={() => {
          // Send the feedback action
          send(createUserFeedback(feedbackPolarity, "trajectory"));

          // Show a toast notification to confirm feedback was sent
          hotToast.success(
            feedbackPolarity === "positive"
              ? t(I18nKey.FEEDBACK$POSITIVE_SENT)
              : t(I18nKey.FEEDBACK$NEGATIVE_SENT),
          );

          // Track the feedback submission
          posthog.capture("feedback_submitted", {
            polarity: feedbackPolarity,
          });

          setFeedbackModalIsOpen(false);
        }}
        polarity={feedbackPolarity}
      />
    </div>
  );
}
