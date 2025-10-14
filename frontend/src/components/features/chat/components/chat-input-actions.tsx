import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { Tools } from "../../controls/tools";
import { usePauseConversation } from "#/hooks/mutation/use-pause-conversation";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

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
  const pauseMutation = usePauseConversation();
  const { data: conversation } = useActiveConversation();

  const handleStopClick = () => {
    // For V1 conversations, use the pause API
    if (conversation?.conversation_version === "V1") {
      pauseMutation.mutate();
    }
    // For V0 conversations or as fallback, use the WebSocket stop event
    else {
      handleStop(onStop);
    }
  };

  return (
    <div className="w-full flex items-center justify-between">
      <div className="flex items-center gap-1">
        <Tools />
        <ServerStatus conversationStatus={conversationStatus} />
      </div>
      <AgentStatus
        className="ml-2 md:ml-3"
        handleStop={handleStopClick}
        handleResumeAgent={handleResumeAgent}
        disabled={disabled}
      />
    </div>
  );
}
