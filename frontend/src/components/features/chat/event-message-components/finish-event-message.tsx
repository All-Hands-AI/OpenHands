import React from "react";
import { ChatMessage } from "../chat-message";
import { MicroagentStatusWrapper } from "./microagent-status-wrapper";
import { LikertScaleWrapper } from "./likert-scale-wrapper";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { MicroagentStatus } from "#/types/microagent-status";
import { ActionEvent, FinishAction } from "#/types/v1/core";

interface FinishEventMessageProps {
  event: ActionEvent<FinishAction>;
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
    tooltip?: string;
  }>;
  isLastMessage: boolean;
  config?: { APP_MODE?: string } | null;
  isCheckingFeedback: boolean;
  feedbackData: {
    exists: boolean;
    rating?: number;
    reason?: string;
  };
}

export function FinishEventMessage({
  event,
  microagentStatus,
  microagentConversationId,
  microagentPRUrl,
  actions,
  isLastMessage,
  config,
  isCheckingFeedback,
  feedbackData,
}: FinishEventMessageProps) {
  return (
    <>
      <ChatMessage
        type="agent"
        message={getEventContent(event).details}
        actions={actions}
      />
      <MicroagentStatusWrapper
        microagentStatus={microagentStatus}
        microagentConversationId={microagentConversationId}
        microagentPRUrl={microagentPRUrl}
        actions={actions}
      />
      <LikertScaleWrapper
        shouldShow={isLastMessage}
        config={config}
        isCheckingFeedback={isCheckingFeedback}
        feedbackData={feedbackData}
      />
    </>
  );
}
