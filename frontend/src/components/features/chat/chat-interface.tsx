import { useSelector, useDispatch } from "react-redux";
import React from "react";
import posthog from "posthog-js";
import { useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import { TrajectoryActions } from "../trajectory/trajectory-actions";
import { createChatMessage } from "#/services/chat-service";
import { InteractiveChatBox } from "./interactive-chat-box";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { isOpenHandsAction } from "#/types/core/guards";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { FeedbackModal } from "../feedback/feedback-modal";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { TypingIndicator } from "./typing-indicator";
import { useWsClient } from "#/context/ws-client-provider";
import { Messages } from "./messages";
import { ChatSuggestions } from "./chat-suggestions";
import { ScrollProvider } from "#/context/scroll-context";

import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { useWSErrorMessage } from "#/hooks/use-ws-error-message";
import { ErrorMessageBanner } from "./error-message-banner";
import { shouldRenderEvent } from "./event-content-helpers/should-render-event";
import { useUploadFiles } from "#/hooks/mutation/use-upload-files";
import { useConfig } from "#/hooks/query/use-config";
import { validateFiles } from "#/utils/file-validation";
import { setMessageToSend } from "#/state/conversation-slice";

function getEntryPoint(
  hasRepository: boolean | null,
  hasReplayJson: boolean | null,
): string {
  if (hasRepository) return "github";
  if (hasReplayJson) return "replay";
  return "direct";
}

export function ChatInterface() {
  const dispatch = useDispatch();
  const { getErrorMessage } = useWSErrorMessage();
  const { send, isLoadingMessages, parsedEvents } = useWsClient();
  const { setOptimisticUserMessage, getOptimisticUserMessage } =
    useOptimisticUserMessage();
  const { t } = useTranslation();
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const {
    scrollDomToBottom,
    onChatBodyScroll,
    hitBottom,
    autoScroll,
    setAutoScroll,
    setHitBottom,
  } = useScrollToBottom(scrollRef);
  const { data: config } = useConfig();

  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive");
  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false);
  const { selectedRepository, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );
  const params = useParams();
  const { mutateAsync: uploadFiles } = useUploadFiles();

  const optimisticUserMessage = getOptimisticUserMessage();
  const errorMessage = getErrorMessage();

  const events = parsedEvents.filter(shouldRenderEvent);

  // Check if there are any substantive agent actions (not just system messages)
  const hasSubstantiveAgentActions = React.useMemo(
    () =>
      parsedEvents.some(
        (event) =>
          isOpenHandsAction(event) &&
          event.source === "agent" &&
          event.action !== "system",
      ),
    [parsedEvents],
  );

  const handleSendMessage = async (
    content: string,
    originalImages: File[],
    originalFiles: File[],
  ) => {
    // Create mutable copies of the arrays
    const images = [...originalImages];
    const files = [...originalFiles];
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

    // Validate file sizes before any processing
    const allFiles = [...images, ...files];
    const validation = validateFiles(allFiles);

    if (!validation.isValid) {
      displayErrorToast(`Error: ${validation.errorMessage}`);
      return; // Stop processing if validation fails
    }

    const promises = images.map((image) => convertImageToBase64(image));
    const imageUrls = await Promise.all(promises);

    const timestamp = new Date().toISOString();

    const { skipped_files: skippedFiles, uploaded_files: uploadedFiles } =
      files.length > 0
        ? await uploadFiles({ conversationId: params.conversationId!, files })
        : { skipped_files: [], uploaded_files: [] };

    skippedFiles.forEach((f) => displayErrorToast(f.reason));

    const filePrompt = `${t("CHAT_INTERFACE$AUGMENTED_PROMPT_FILES_TITLE")}: ${uploadedFiles.join("\n\n")}`;
    const prompt =
      uploadedFiles.length > 0 ? `${content}\n\n${filePrompt}` : content;

    send(createChatMessage(prompt, imageUrls, uploadedFiles, timestamp));
    setOptimisticUserMessage(content);
    dispatch(setMessageToSend(null));
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

  const isWaitingForUserInput =
    curAgentState === AgentState.AWAITING_USER_INPUT ||
    curAgentState === AgentState.FINISHED;

  // Create a ScrollProvider with the scroll hook values
  const scrollProviderValue = {
    scrollRef,
    autoScroll,
    setAutoScroll,
    scrollDomToBottom,
    hitBottom,
    setHitBottom,
    onChatBodyScroll,
  };

  return (
    <ScrollProvider value={scrollProviderValue}>
      <div className="h-full flex flex-col justify-between pr-0 md:pr-4 relative">
        {!hasSubstantiveAgentActions &&
          !optimisticUserMessage &&
          !events.some(
            (event) => isOpenHandsAction(event) && event.source === "user",
          ) && (
            <ChatSuggestions
              onSuggestionsClick={(message) =>
                dispatch(setMessageToSend(message))
              }
            />
          )}
        {/* Note: We only hide chat suggestions when there's a user message */}

        <div
          ref={scrollRef}
          onScroll={(e) => onChatBodyScroll(e.currentTarget)}
          className="custom-scrollbar-always flex flex-col grow overflow-y-auto overflow-x-hidden px-4 pt-4 gap-2 fast-smooth-scroll"
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
        </div>

        <div className="flex flex-col gap-[6px]">
          <div className="flex justify-between relative">
            {events.length > 0 && (
              <TrajectoryActions
                onPositiveFeedback={() =>
                  onClickShareFeedbackActionButton("positive")
                }
                onNegativeFeedback={() =>
                  onClickShareFeedbackActionButton("negative")
                }
                isSaasMode={config?.APP_MODE === "saas"}
              />
            )}

            <div className="absolute left-1/2 transform -translate-x-1/2 bottom-0">
              {curAgentState === AgentState.RUNNING && <TypingIndicator />}
            </div>

            {!hitBottom && <ScrollToBottomButton onClick={scrollDomToBottom} />}
          </div>

          {errorMessage && <ErrorMessageBanner message={errorMessage} />}

          <InteractiveChatBox
            onSubmit={handleSendMessage}
            onStop={handleStop}
            isWaitingForUserInput={isWaitingForUserInput}
            hasSubstantiveAgentActions={hasSubstantiveAgentActions}
            optimisticUserMessage={!!optimisticUserMessage}
          />
        </div>

        {config?.APP_MODE !== "saas" && (
          <FeedbackModal
            isOpen={feedbackModalIsOpen}
            onClose={() => setFeedbackModalIsOpen(false)}
            polarity={feedbackPolarity}
          />
        )}
      </div>
    </ScrollProvider>
  );
}
