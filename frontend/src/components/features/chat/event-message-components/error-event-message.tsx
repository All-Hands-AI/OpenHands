import React from "react";
import { ErrorMessage } from "../error-message";
import { MicroagentStatusWrapper } from "./microagent-status-wrapper";
import { LikertScaleWrapper } from "./likert-scale-wrapper";
import { MicroagentStatus } from "#/types/microagent-status";

interface ErrorEventMessageProps {
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
    tooltip?: string;
  }>;
  isInLast10Actions: boolean;
  config?: { APP_MODE?: string } | null;
  isCheckingFeedback: boolean;
  feedbackData: {
    exists: boolean;
    rating?: number;
    reason?: string;
  };
}

export function ErrorEventMessage({
  microagentStatus,
  microagentConversationId,
  microagentPRUrl,
  actions,
  isInLast10Actions,
  config,
  isCheckingFeedback,
  feedbackData,
}: ErrorEventMessageProps) {
  return (
    <div>
      <ErrorMessage errorId={errorId} defaultMessage={errorMessage} />
      <MicroagentStatusWrapper
        microagentStatus={microagentStatus}
        microagentConversationId={microagentConversationId}
        microagentPRUrl={microagentPRUrl}
        actions={actions}
      />
      <LikertScaleWrapper
        shouldShow={isInLast10Actions}
        config={config}
        isCheckingFeedback={isCheckingFeedback}
        feedbackData={feedbackData}
      />
    </div>
  );
}
