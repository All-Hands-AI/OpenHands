import React from "react";
import { ChatMessage } from "../chat-message";
import { MicroagentStatusWrapper } from "./microagent-status-wrapper";
import { MicroagentStatus } from "#/types/microagent-status";

interface ObservationPairEventMessageProps {
  event: { thought: string };
  microagentStatus?: MicroagentStatus | null;
  microagentConversationId?: string;
  microagentPRUrl?: string;
  actions?: Array<{
    icon: React.ReactNode;
    onClick: () => void;
    tooltip?: string;
  }>;
}

export function ObservationPairEventMessage({
  event,
  microagentStatus,
  microagentConversationId,
  microagentPRUrl,
  actions,
}: ObservationPairEventMessageProps) {
  if (event.thought) {
    return (
      <div>
        <ChatMessage type="agent" message={event.thought} actions={actions} />
        <MicroagentStatusWrapper
          microagentStatus={microagentStatus}
          microagentConversationId={microagentConversationId}
          microagentPRUrl={microagentPRUrl}
          actions={actions}
        />
      </div>
    );
  }

  return (
    <MicroagentStatusWrapper
      microagentStatus={microagentStatus}
      microagentConversationId={microagentConversationId}
      microagentPRUrl={microagentPRUrl}
      actions={actions}
    />
  );
}
