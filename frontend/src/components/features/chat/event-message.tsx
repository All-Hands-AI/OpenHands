import React from "react";
import { MicroagentStatus } from "#/types/microagent-status";
import { useConfig } from "#/hooks/query/use-config";
import { useFeedbackExists } from "#/hooks/query/use-feedback-exists";
import {
  ErrorEventMessage,
  UserAssistantEventMessage,
  FinishEventMessage,
  RejectEventMessage,
  McpEventMessage,
  TaskTrackingEventMessage,
  ObservationPairEventMessage,
  GenericEventMessageWrapper,
} from "./event-message-components";
import { OpenHandsEvent } from "#/types/v1/core";
import {
  isActionEvent,
  isAgentErrorEvent,
  isAssistantMessageEvent,
  isFinishActionEvent,
  isMCPToolObservation,
  isTaskTrackerObservation,
  isUserMessageEvent,
  isUserRejectObservation,
} from "#/types/v1/type-guards";

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

  const {
    data: feedbackData = { exists: false },
    isLoading: isCheckingFeedback,
  } = useFeedbackExists(event.id);

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

  // Error observations
  if (isAgentErrorEvent(event)) {
    return (
      <ErrorEventMessage
        event={{
          errorId: event.error,
          errorMessage: event.error,
        }}
        {...commonProps}
      />
    );
  }

  // Observation pairs with OpenHands actions
  if (hasObservationPair && isActionEvent(event)) {
    return (
      <ObservationPairEventMessage
        event={{
          thought: event.thought[0].text,
        }}
        microagentStatus={microagentStatus}
        microagentConversationId={microagentConversationId}
        microagentPRUrl={microagentPRUrl}
        actions={actions}
      />
    );
  }

  // Finish actions
  if (isFinishActionEvent(event)) {
    return <FinishEventMessage event={event} {...commonProps} />;
  }

  // User and assistant messages
  // TODO: Split into separate components?
  if (isUserMessageEvent(event) || isAssistantMessageEvent(event)) {
    return (
      <UserAssistantEventMessage
        event={event}
        shouldShowConfirmationButtons={shouldShowConfirmationButtons}
        {...commonProps}
      />
    );
  }

  // Reject observations
  if (isUserRejectObservation(event)) {
    return (
      <RejectEventMessage
        event={{
          message: event.rejection_reason,
        }}
      />
    );
  }

  // MCP observations
  if (isMCPToolObservation(event)) {
    return (
      <McpEventMessage
        event={event}
        shouldShowConfirmationButtons={shouldShowConfirmationButtons}
      />
    );
  }

  // Task tracking observations
  if (isTaskTrackerObservation(event)) {
    return (
      <TaskTrackingEventMessage
        event={event}
        shouldShowConfirmationButtons={shouldShowConfirmationButtons}
      />
    );
  }

  // Generic fallback
  return (
    <GenericEventMessageWrapper
      event={event}
      shouldShowConfirmationButtons={shouldShowConfirmationButtons}
    />
  );
}
