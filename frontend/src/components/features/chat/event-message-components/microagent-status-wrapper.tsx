import React from "react";
import { MicroagentStatus } from "#/types/microagent-status";
import { MicroagentStatusIndicator } from "../microagent/microagent-status-indicator";

interface MicroagentStatusWrapperProps {
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
    tooltip?: string;
  }>;
}

export function MicroagentStatusWrapper({
  microagentStatus,
  microagentConversationId,
  microagentPRUrl,
  actions,
}: MicroagentStatusWrapperProps) {
  if (!microagentStatus || !actions) {
    return null;
  }

  return (
    <MicroagentStatusIndicator
      status={microagentStatus}
      conversationId={microagentConversationId}
      prUrl={microagentPRUrl}
    />
  );
}
