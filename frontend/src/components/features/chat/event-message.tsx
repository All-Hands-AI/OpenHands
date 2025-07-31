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
import { MicroagentStatus } from "#/types/microagent-status";
import { MicroagentStatusIndicator } from "./microagent/microagent-status-indicator";
import { FileList } from "../files/file-list";
import { parseMessageFromEvent } from "./event-content-helpers/parse-message-from-event";
import { LikertScale } from "../feedback/likert-scale";

import { useConfig } from "#/hooks/query/use-config";
import { useFeedbackExists } from "#/hooks/query/use-feedback-exists";

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

interface EventMessageProps {
  event: OpenHandsAction | OpenHandsObservation;
  hasObservationPair: boolean;
  isAwaitingUserConfirmation: boolean;
  isLastMessage: boolean;
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
  }>;
  isInLast10Actions: boolean;
}

export function EventMessage({
  event,
  hasObservationPair,
  isAwaitingUserConfirmation,
  isLastMessage,
  microagentStatus,
  microagentConversationId,
  microagentPRUrl,
  actions,
  isInLast10Actions,
}: EventMessageProps) {
  const shouldShowConfirmationButtons =
    isLastMessage && event.source === "agent" && isAwaitingUserConfirmation;

  const { data: config } = useConfig();

  const {
    data: feedbackData = { exists: false },
    isLoading: isCheckingFeedback,
  } = useFeedbackExists(event.id);

  const renderLikertScale = () => {
    if (config?.APP_MODE !== "saas" || isCheckingFeedback) {
      return null;
    }

    // For error observations, show if in last 10 actions
    // For other events, show only if it's the last message
    const shouldShow = isErrorObservation(event)
      ? isInLast10Actions
      : isLastMessage;

    if (!shouldShow) {
      return null;
    }

    return (
      <LikertScale
        eventId={event.id}
        initiallySubmitted={feedbackData.exists}
        initialRating={feedbackData.rating}
        initialReason={feedbackData.reason}
      />
    );
  };

  if (isErrorObservation(event)) {
    return (
      <div>
        <ErrorMessage
          errorId={event.extras.error_id}
          defaultMessage={event.message}
        />
        {microagentStatus && actions && (
          <MicroagentStatusIndicator
            status={microagentStatus}
            conversationId={microagentConversationId}
            prUrl={microagentPRUrl}
          />
        )}
        {renderLikertScale()}
      </div>
    );
  }

  if (hasObservationPair && isOpenHandsAction(event)) {
    if (hasThoughtProperty(event.args)) {
      return (
        <div>
          <ChatMessage
            type="agent"
            message={event.args.thought}
            actions={actions}
          />
          {microagentStatus && actions && (
            <MicroagentStatusIndicator
              status={microagentStatus}
              conversationId={microagentConversationId}
              prUrl={microagentPRUrl}
            />
          )}
        </div>
      );
    }
    return microagentStatus && actions ? (
      <MicroagentStatusIndicator
        status={microagentStatus}
        conversationId={microagentConversationId}
        prUrl={microagentPRUrl}
      />
    ) : null;
  }

  if (isFinishAction(event)) {
    return (
      <>
        <ChatMessage
          type="agent"
          message={getEventContent(event).details}
          actions={actions}
        />
        {microagentStatus && actions && (
          <MicroagentStatusIndicator
            status={microagentStatus}
            conversationId={microagentConversationId}
            prUrl={microagentPRUrl}
          />
        )}
        {renderLikertScale()}
      </>
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    const message = parseMessageFromEvent(event);

    return (
      <>
        <ChatMessage type={event.source} message={message} actions={actions}>
          {event.args.image_urls && event.args.image_urls.length > 0 && (
            <ImageCarousel size="small" images={event.args.image_urls} />
          )}
          {event.args.file_urls && event.args.file_urls.length > 0 && (
            <FileList files={event.args.file_urls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
        {microagentStatus && actions && (
          <MicroagentStatusIndicator
            status={microagentStatus}
            conversationId={microagentConversationId}
            prUrl={microagentPRUrl}
          />
        )}
        {isAssistantMessage(event) &&
          event.action === "message" &&
          renderLikertScale()}
      </>
    );
  }

  if (isRejectObservation(event)) {
    return (
      <div>
        <ChatMessage type="agent" message={event.content} />
      </div>
    );
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
