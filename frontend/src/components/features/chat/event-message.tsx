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
} from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { ImageCarousel } from "../images/image-carousel";
import { ChatMessage } from "./chat-message";
import { ErrorMessage } from "./error-message";
import { MCPObservationContent } from "./mcp-observation-content";
import { getObservationResult } from "./event-content-helpers/get-observation-result";
import { getEventContent } from "./event-content-helpers/get-event-content";
import { GenericEventMessage } from "./generic-event-message";
import { LikertScale } from "../feedback/likert-scale";

import { useConfig } from "#/hooks/query/use-config";
import { useConversationId } from "#/hooks/use-conversation-id";
import OpenHands from "#/api/open-hands";

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

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

  // We don't need parsedEvents from useWsClient() anymore
  const { data: config } = useConfig();
  const { conversationId } = useConversationId();

  // State to track feedback submission status
  const [feedbackState, setFeedbackState] = React.useState<{
    submitted: boolean;
    rating?: number;
    reason?: string;
  }>({ submitted: false });

  // We no longer check for feedback in the event stream since we're using the database
  // Instead, we'll rely on local state to track if feedback has been submitted for this session

  const handleRatingSubmit = async (rating: number, reason?: string) => {
    try {
      // Submit feedback to our new endpoint instead of the event stream
      await OpenHands.submitConversationFeedback(
        conversationId,
        rating,
        event.id, // Pass the event ID this feedback corresponds to
        reason,
      );

      // Update local state to reflect that feedback has been submitted
      setFeedbackState({
        submitted: true,
        rating,
        reason,
      });
    } catch (error) {
      // Log error but continue - user will just see the UI stay in unsubmitted state
      // eslint-disable-next-line no-console
      console.error(i18n.t("FEEDBACK$FAILED_TO_SUBMIT"), error);
    }
  };

  if (isErrorObservation(event)) {
    return (
      <ErrorMessage
        errorId={event.extras.error_id}
        defaultMessage={event.message}
      />
    );
  }

  if (hasObservationPair && isOpenHandsAction(event)) {
    if (hasThoughtProperty(event.args)) {
      return <ChatMessage type="agent" message={event.args.thought} />;
    }
    return null;
  }

  // Show Likert scale for agent messages if:
  // 1. It's in SaaS mode, AND
  // 2. It's the last message OR feedback has already been submitted for this message
  const showLikertScale =
    config?.APP_MODE === "saas" &&
    isAssistantMessage(event) &&
    (isLastMessage || feedbackState.submitted);

  if (isFinishAction(event)) {
    return (
      <>
        <ChatMessage type="agent" message={getEventContent(event).details} />
        {showLikertScale && (
          <LikertScale
            onRatingSubmit={handleRatingSubmit}
            initiallySubmitted={feedbackState.submitted}
            initialRating={feedbackState.rating}
            initialReason={feedbackState.reason}
          />
        )}
      </>
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    return (
      <>
        <ChatMessage
          type={event.source}
          message={isUserMessage(event) ? event.args.content : event.message}
        >
          {event.args.image_urls && event.args.image_urls.length > 0 && (
            <ImageCarousel size="small" images={event.args.image_urls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
        {showLikertScale && (
          <LikertScale
            onRatingSubmit={handleRatingSubmit}
            initiallySubmitted={feedbackState.submitted}
            initialRating={feedbackState.rating}
            initialReason={feedbackState.reason}
          />
        )}
      </>
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
