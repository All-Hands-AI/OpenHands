import { ConversationStatus as ConversationStatusType } from "#/types/conversation-status";
import { ConnectionStatus } from "./connection-status";
import { RuntimeStatus } from "./runtime-status";
import { ConversationStatus } from "./conversation-status";
import { AgentStatus } from "./agent-status";
import { cn } from "#/utils/utils";

export interface StatusBarProps {
  className?: string;
  conversationStatus: ConversationStatusType | null;
}

export function StatusBar({
  className = "",
  conversationStatus,
}: StatusBarProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Connection Status - WebSocket connection */}
      <ConnectionStatus />

      {/* Conversation Status - Conversation state */}
      <ConversationStatus conversationStatus={conversationStatus} />

      {/* Runtime Status - Runtime environment */}
      <RuntimeStatus />

      {/* Agent Status - Agent execution */}
      <AgentStatus />
    </div>
  );
}

export default StatusBar;
