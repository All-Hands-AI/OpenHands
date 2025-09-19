import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { Tools } from "../../controls/tools";

interface ChatInputActionsProps {
  conversationStatus: ConversationStatus | null;
  disabled: boolean;
  handleStop: (onStop?: () => void) => void;
  handleResumeAgent: () => void;
  onStop?: () => void;
}

export function ChatInputActions({
  conversationStatus,
  disabled,
  handleStop,
  handleResumeAgent,
  onStop,
}: ChatInputActionsProps) {
  return (
    <div className="w-full flex items-center justify-between">
      <div className="flex items-center gap-1">
        <Tools />
        <ServerStatus conversationStatus={conversationStatus} />
      </div>
      <AgentStatus
        handleStop={() => handleStop(onStop)}
        handleResumeAgent={handleResumeAgent}
        disabled={disabled}
      />
    </div>
  );
}
