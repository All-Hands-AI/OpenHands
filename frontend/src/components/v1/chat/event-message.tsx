import React from "react";
import { OpenHandsEvent, MessageEvent, ActionEvent } from "#/types/v1/core";
import { FinishAction } from "#/types/v1/core/base/action";
import {
  isActionEvent,
  isObservationEvent,
  isAgentErrorEvent,
} from "#/types/v1/type-guards";
import { MicroagentStatus } from "#/types/microagent-status";
import { useConfig } from "#/hooks/query/use-config";
// TODO: Implement V1 feedback functionality when API supports V1 event IDs
// import { useFeedbackExists } from "#/hooks/query/use-feedback-exists";
import {
  ErrorEventMessage,
  UserAssistantEventMessage,
  FinishEventMessage,
  ObservationPairEventMessage,
  GenericEventMessageWrapper,
} from "./event-message-components";

interface EventMessageProps {
  event: OpenHandsEvent;
  hasObservationPair: boolean;
  isAwaitingUserConfirmation: boolean;
  isLastMessage: boolean;
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
    tooltip?: string;
  }>;
  isInLast10Actions: boolean;
}

/* eslint-disable react/jsx-props-no-spreading */
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

  // V1 events use string IDs, but useFeedbackExists expects number
  // For now, we'll skip feedback functionality for V1 events
  const feedbackData = { exists: false };
  const isCheckingFeedback = false;

  // Common props for components that need them
  const commonProps = {
    microagentStatus,
    microagentConversationId,
    microagentPRUrl,
    actions,
    isLastMessage,
    isInLast10Actions,
    config,
    isCheckingFeedback,
    feedbackData,
  };

  // Agent error events
  if (isAgentErrorEvent(event)) {
    return <ErrorEventMessage event={event} {...commonProps} />;
  }

  // Observation pairs with actions
  if (hasObservationPair && isActionEvent(event)) {
    return (
      <ObservationPairEventMessage
        event={event}
        microagentStatus={microagentStatus}
        microagentConversationId={microagentConversationId}
        microagentPRUrl={microagentPRUrl}
        actions={actions}
      />
    );
  }

  // Finish actions
  if (isActionEvent(event) && event.action.kind === "FinishAction") {
    return (
      <FinishEventMessage
        event={event as ActionEvent<FinishAction>}
        {...commonProps}
      />
    );
  }

  // Message events (user and assistant messages)
  if (!isActionEvent(event) && !isObservationEvent(event)) {
    // This is a MessageEvent
    return (
      <UserAssistantEventMessage
        event={event as MessageEvent}
        shouldShowConfirmationButtons={shouldShowConfirmationButtons}
        {...commonProps}
      />
    );
  }

  // Generic fallback for all other events (including observation events)
  return (
    <GenericEventMessageWrapper
      event={event}
      shouldShowConfirmationButtons={shouldShowConfirmationButtons}
    />
  );
}
