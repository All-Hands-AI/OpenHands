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
  isUserFeedbackAction,
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
import { useWsClient } from "#/context/ws-client-provider";

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

  const { send, parsedEvents } = useWsClient();

  // Check if there's already a UserFeedbackAction in the event stream for this event
  const hasFeedbackBeenSubmitted = React.useMemo(() => {
    if (!parsedEvents) return false;

    // Check if there's a user_feedback action for this specific event ID
    return parsedEvents.some(
      (e) => isUserFeedbackAction(e) && e.args.event_id === event.id,
    );
  }, [event.id, parsedEvents]);

  const handleRatingSubmit = (rating: number, reason?: string) => {
    // Send the user feedback action to the event stream
    send({
      action: "user_feedback",
      source: "user",
      args: {
        rating,
        reason,
        event_id: event.id, // Add the event ID to track which event this feedback corresponds to
      },
    });
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

  if (isFinishAction(event)) {
    return (
      <>
        <ChatMessage type="agent" message={getEventContent(event).details} />
        <LikertScale
          onRatingSubmit={handleRatingSubmit}
          initiallySubmitted={hasFeedbackBeenSubmitted}
        />
      </>
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    // Only show Likert scale for agent messages that are not finish actions
    // and are the last message in the conversation
    const showLikertScale = isAssistantMessage(event);

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
            initiallySubmitted={hasFeedbackBeenSubmitted}
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
