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

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

interface EventMessageProps {
  event: OpenHandsAction | OpenHandsObservation;
  hasObservationPair: boolean;
  isAwaitingUserConfirmation: boolean;
  isLastMessage: boolean;
  microagentStatus?: MicroagentStatus | null;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
  }>;
}

export function EventMessage({
  event,
  hasObservationPair,
  isAwaitingUserConfirmation,
  isLastMessage,
  microagentStatus,
  actions,
}: EventMessageProps) {
  const shouldShowConfirmationButtons =
    isLastMessage && event.source === "agent" && isAwaitingUserConfirmation;

  if (isErrorObservation(event)) {
    return (
      <div>
        <ErrorMessage
          errorId={event.extras.error_id}
          defaultMessage={event.message}
        />
        {microagentStatus && actions && (
          <MicroagentStatusIndicator status={microagentStatus} />
        )}
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
            <MicroagentStatusIndicator status={microagentStatus} />
          )}
        </div>
      );
    }
    return microagentStatus && actions ? (
      <MicroagentStatusIndicator status={microagentStatus} />
    ) : null;
  }

  if (isFinishAction(event)) {
    return (
      <div>
        <ChatMessage
          type="agent"
          message={getEventContent(event).details}
          actions={actions}
        />
        {microagentStatus && actions && (
          <MicroagentStatusIndicator status={microagentStatus} />
        )}
      </div>
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    return (
      <div>
        <ChatMessage
          type={event.source}
          message={isUserMessage(event) ? event.args.content : event.message}
          actions={actions}
        >
          {event.args.image_urls && event.args.image_urls.length > 0 && (
            <ImageCarousel size="small" images={event.args.image_urls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
        {microagentStatus && actions && (
          <MicroagentStatusIndicator status={microagentStatus} />
        )}
      </div>
    );
  }

  if (isRejectObservation(event)) {
    return (
      <div>
        <ChatMessage type="agent" message={event.content} />
        {microagentStatus && actions && (
          <MicroagentStatusIndicator status={microagentStatus} />
        )}
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
        {microagentStatus && actions && (
          <MicroagentStatusIndicator status={microagentStatus} />
        )}
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
      {microagentStatus && actions && (
        <MicroagentStatusIndicator status={microagentStatus} />
      )}
    </div>
  );
}
