import { useQueryClient } from "@tanstack/react-query";
import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { Tools } from "../../controls/tools";
import { useUnifiedStopConversation } from "#/hooks/mutation/use-unified-stop-conversation";
import { useConversationId } from "#/hooks/use-conversation-id";

interface ChatInputActionsProps {
  conversationStatus: ConversationStatus | null;
  disabled: boolean;
  handleResumeAgent: () => void;
}

export function ChatInputActions({
  conversationStatus,
  disabled,
  handleResumeAgent,
}: ChatInputActionsProps) {
  const queryClient = useQueryClient();
  const stopMutation = useUnifiedStopConversation();
  const { conversationId } = useConversationId();

  const handleStopClick = () => {
    stopMutation.mutate({ conversationId });
  };

  // Check if ANY stop conversation mutation is pending globally
  const mutationCache = queryClient.getMutationCache();
  const stopMutations = mutationCache.findAll({
    mutationKey: ["stop-conversation"],
  });
  const isAnyStopPending = stopMutations.some(
    (mutation) => mutation.state.status === "pending",
  );

  const isPausing = stopMutation.isPending || isAnyStopPending;

  return (
    <div className="w-full flex items-center justify-between">
      <div className="flex items-center gap-1">
        <Tools />
        <ServerStatus
          conversationStatus={conversationStatus}
          isPausing={isPausing}
        />
      </div>
      <AgentStatus
        className="ml-2 md:ml-3"
        handleStop={handleStopClick}
        handleResumeAgent={handleResumeAgent}
        disabled={disabled}
        isPausing={isPausing}
      />
    </div>
  );
}
