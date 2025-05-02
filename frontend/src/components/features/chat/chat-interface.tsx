import { useDispatch, useSelector } from "react-redux";
import React from "react";
import posthog from "posthog-js";
import { useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { TrajectoryActions } from "../trajectory/trajectory-actions";
import { TrajectorySummary } from "../trajectory/trajectory-summary";
import { createChatMessage } from "#/services/chat-service";
import { InteractiveChatBox } from "./interactive-chat-box";
import { addUserMessage } from "#/state/chat-slice";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { FeedbackModal } from "../feedback/feedback-modal";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { TypingIndicator } from "./typing-indicator";
import { useWsClient } from "#/context/ws-client-provider";
import { Messages } from "./messages";
import { ChatSuggestions } from "./chat-suggestions";
import { ActionSuggestions } from "./action-suggestions";

import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useGetTrajectory } from "#/hooks/mutation/use-get-trajectory";
import { useGetTrajectorySummary } from "#/hooks/mutation/use-get-trajectory-summary";
import { downloadTrajectory } from "#/utils/download-trajectory";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { TrajectorySummarySegment } from "#/api/open-hands.types";

function getEntryPoint(
  hasRepository: boolean | null,
  hasReplayJson: boolean | null,
): string {
  if (hasRepository) return "github";
  if (hasReplayJson) return "replay";
  return "direct";
}

export function ChatInterface() {
  const { send, isLoadingMessages } = useWsClient();
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
  const { mutate: getTrajectorySummary } = useGetTrajectorySummary();

  // State for trajectory summary
  const [showSummary, setShowSummary] = React.useState(false);
  const [overallSummary, setOverallSummary] = React.useState("");
  const [summarySegments, setSummarySegments] = React.useState<
    TrajectorySummarySegment[]
  >([]);
  const [userMessageCount, setUserMessageCount] = React.useState(0);
  const [lastSummarizedCount, setLastSummarizedCount] = React.useState(0);

  // Count user messages
  React.useEffect(() => {
    const userMessages = messages.filter((msg) => msg.sender === "user");
    setUserMessageCount(userMessages.length);
  }, [messages]);

  // Trigger summarization after every 2 user messages
  React.useEffect(() => {
    const shouldSummarize =
      userMessageCount > 0 &&
      userMessageCount % 2 === 0 &&
      userMessageCount !== lastSummarizedCount &&
      curAgentState !== AgentState.RUNNING;

    // Check if summarization should be triggered

    if (shouldSummarize && params.conversationId) {
      const { conversationId } = params;
      // Attempt to summarize conversation
      getTrajectorySummary(conversationId, {
        onSuccess: (data) => {
          // Summary received
          setOverallSummary(data.overall_summary);
          setSummarySegments(data.segments);
          setShowSummary(true);
          setLastSummarizedCount(userMessageCount);
        },
        onError: () => {
          // Handle error fetching summary
        },
      });
    }
  }, [
    userMessageCount,
    lastSummarizedCount,
    curAgentState,
    params.conversationId,
    getTrajectorySummary,
  ]);

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

        {!isLoadingMessages && !showSummary && (
          <Messages
            messages={messages}
            isAwaitingUserConfirmation={
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION
            }
          />
        )}

        {!isLoadingMessages && showSummary && (
          <TrajectorySummary
            overallSummary={overallSummary}
            segments={summarySegments}
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
          <div className="flex items-center gap-2">
            <TrajectoryActions
              onPositiveFeedback={() =>
                onClickShareFeedbackActionButton("positive")
              }
              onNegativeFeedback={() =>
                onClickShareFeedbackActionButton("negative")
              }
              onExportTrajectory={() => onClickExportTrajectoryButton()}
            />

            {/* Summary Toggle Button - only show if summary is available */}
            {summarySegments.length > 0 && (
              <button
                type="button"
                onClick={() => setShowSummary(!showSummary)}
                className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-tertiary hover:bg-base-secondary transition-colors text-content"
                title={
                  showSummary
                    ? "Show original messages"
                    : "Show conversation summary"
                }
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                {showSummary ? "Original View" : "Summary View"}
              </button>
            )}

            {/* Manual Summarize Button - only show in summary view
            {params.conversationId && showSummary && (
              <button
                type="button"
                onClick={() => {
                  const { conversationId } = params;
                  if (!conversationId) return;

                  // Manual summarize clicked - will include all messages up to this point
                  getTrajectorySummary(conversationId, {
                    onSuccess: (data) => {
                      // Summary received
                      setOverallSummary(data.overall_summary);
                      setSummarySegments(data.segments);
                      setShowSummary(true);
                      setLastSummarizedCount(userMessageCount);
                    },
                    onError: () => {
                      // Handle error
                    },
                  });
                }}
                className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-tertiary hover:bg-base-secondary transition-colors text-content border border-tertiary"
                title="Resummarize conversation up to this point"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4 5a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zm0 6a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zm0 6a1 1 0 011-1h6a1 1 0 110 2H5a1 1 0 01-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                Resummarize
              </button>
            )} */}
          </div>

          <div className="absolute left-1/2 transform -translate-x-1/2 bottom-0">
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
