import React from "react";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { OpenHandsAction } from "#/types/core/actions";
import {
  isUserMessage,
  isErrorObservation,
  isAssistantMessage,
  isOpenHandsAction,
  isOpenHandsObservation,
  isFinishAction,
  isRejectObservation,
  isMcpObservation,
  isAgentStateChangeObservation,
} from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { ImageCarousel } from "../images/image-carousel";
import { ChatMessage } from "./chat-message";
import { ErrorMessage } from "./error-message";
import { MCPObservationContent } from "./mcp-observation-content";
import { getObservationResult } from "./event-content-helpers/get-observation-result";
import { getEventContent } from "./event-content-helpers/get-event-content";
import { GenericEventMessage } from "./generic-event-message";
import { FileList } from "../files/file-list";
import { parseMessageFromEvent } from "./event-content-helpers/parse-message-from-event";
import { LikertScale } from "../feedback/likert-scale";
import { AgentState } from "#/types/agent-state";

import { useConfig } from "#/hooks/query/use-config";
import { useFeedbackExists } from "#/hooks/query/use-feedback-exists";

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

// Helper function to determine if we should show feedback for an agent state change
const shouldShowFeedbackForAgentState = (state: string): boolean =>
  state === AgentState.AWAITING_USER_INPUT || state === AgentState.ERROR;

interface EventMessageProps {
  event: OpenHandsAction | OpenHandsObservation;
  hasObservationPair: boolean;
  isAwaitingUserConfirmation: boolean;
  isLastMessage: boolean;
}

export function EventMessage({
  event,
  hasObservationPair,
  isAwaitingUserConfirmation,
  isLastMessage,
}: EventMessageProps) {
  const shouldShowConfirmationButtons =
    isLastMessage && event.source === "agent" && isAwaitingUserConfirmation;

  const { data: config } = useConfig();

  // Use our query hook to check if feedback exists and get rating/reason
  let eventIdForFeedback: number | undefined;

  if (
    (isAgentStateChangeObservation(event) &&
      shouldShowFeedbackForAgentState(event.extras.agent_state)) ||
    isFinishAction(event) ||
    isErrorObservation(event) ||
    (isAssistantMessage(event) && event.action === "message")
  ) {
    eventIdForFeedback = event.id;
  }

  const {
    data: feedbackData = { exists: false },
    isLoading: isCheckingFeedback,
  } = useFeedbackExists(eventIdForFeedback);

  // Define all Likert scale conditions before using them
  const showLikertScaleForErrorObservation =
    config?.APP_MODE === "saas" &&
    isErrorObservation(event) &&
    isLastMessage &&
    !isCheckingFeedback;

  if (isErrorObservation(event)) {
    return (
      <div>
        <ErrorMessage
          errorId={event.extras.error_id}
          defaultMessage={event.message}
        />
        {showLikertScaleForErrorObservation && (
          <LikertScale
            eventId={event.id}
            initiallySubmitted={feedbackData.exists}
            initialRating={feedbackData.rating}
            initialReason={feedbackData.reason}
          />
        )}
      </div>
    );
  }

  if (hasObservationPair && isOpenHandsAction(event)) {
    if (hasThoughtProperty(event.args)) {
      return <ChatMessage type="agent" message={event.args.thought} />;
    }
    return null;
  }

  // Check if we should show the Likert scale for agent state change
  const showLikertScaleForStateChange =
    config?.APP_MODE === "saas" &&
    isAgentStateChangeObservation(event) &&
    shouldShowFeedbackForAgentState(event.extras.agent_state) &&
    isLastMessage &&
    !isCheckingFeedback;

  // Check if we should show the Likert scale for finish action
  const showLikertScaleForFinishAction =
    config?.APP_MODE === "saas" &&
    isFinishAction(event) &&
    isLastMessage &&
    !isCheckingFeedback;

  if (isFinishAction(event)) {
    return (
      <div>
        <ChatMessage type="agent" message={getEventContent(event).details} />
        {showLikertScaleForFinishAction && (
          <LikertScale
            eventId={event.id}
            initiallySubmitted={feedbackData.exists}
            initialRating={feedbackData.rating}
            initialReason={feedbackData.reason}
          />
        )}
      </div>
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    const message = parseMessageFromEvent(event);

    // Check if we should show the Likert scale for assistant message (awaiting user input)
    const showLikertScaleForAssistantMessage =
      config?.APP_MODE === "saas" &&
      isAssistantMessage(event) &&
      event.action === "message" &&
      isLastMessage &&
      !isCheckingFeedback;

    return (
      <div>
        <ChatMessage type={event.source} message={message}>
          {event.args.image_urls && event.args.image_urls.length > 0 && (
            <ImageCarousel size="small" images={event.args.image_urls} />
          )}
          {event.args.file_urls && event.args.file_urls.length > 0 && (
            <FileList files={event.args.file_urls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
        {showLikertScaleForAssistantMessage && (
          <LikertScale
            eventId={event.id}
            initiallySubmitted={feedbackData.exists}
            initialRating={feedbackData.rating}
            initialReason={feedbackData.reason}
          />
        )}
      </div>
    );
  }

  if (isRejectObservation(event)) {
    return <ChatMessage type="agent" message={event.content} />;
  }

  if (isMcpObservation(event)) {
    return (
      <div>
        <GenericEventMessage
          title={getEventContent(event).title}
          details={<MCPObservationContent event={event} />}
          success={getObservationResult(event)}
        />
        {shouldShowConfirmationButtons && <ConfirmationButtons />}
      </div>
    );
  }

  // Handle agent state change observation with feedback
  if (isAgentStateChangeObservation(event)) {
    return (
      <div>
        <GenericEventMessage
          title={getEventContent(event).title}
          details={getEventContent(event).details}
          success={getObservationResult(event)}
        />
        {showLikertScaleForStateChange && (
          <LikertScale
            eventId={event.id}
            initiallySubmitted={feedbackData.exists}
            initialRating={feedbackData.rating}
            initialReason={feedbackData.reason}
          />
        )}
        {shouldShowConfirmationButtons && <ConfirmationButtons />}
      </div>
    );
  }

  return (
    <div>
      {isOpenHandsAction(event) && hasThoughtProperty(event.args) && (
        <ChatMessage type="agent" message={event.args.thought} />
      )}

      <GenericEventMessage
        title={getEventContent(event).title}
        details={getEventContent(event).details}
        success={
          isOpenHandsObservation(event)
            ? getObservationResult(event)
            : undefined
        }
      />

      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
