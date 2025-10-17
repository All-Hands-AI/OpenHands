import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { Tools } from "../../controls/tools";
import { useUnifiedPauseConversationSandbox } from "#/hooks/mutation/use-unified-stop-conversation";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useUnifiedResumeConversationSandbox } from "#/hooks/mutation/use-unified-start-conversation";
import { useUserProviders } from "#/hooks/use-user-providers";

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
  const pauseConversationSandboxMutation = useUnifiedPauseConversationSandbox();
  const resumeConversationSandboxMutation =
    useUnifiedResumeConversationSandbox();
  const { conversationId } = useConversationId();
  const { providers } = useUserProviders();

  const handleStopClick = () => {
    pauseConversationSandboxMutation.mutate({ conversationId });
  };

  const handleStartClick = () => {
    resumeConversationSandboxMutation.mutate({ conversationId, providers });
  };

  const isPausing = pauseConversationSandboxMutation.isPending;

  return (
    <div className="w-full flex items-center justify-between">
      <div className="flex items-center gap-1">
        <Tools />
        <ServerStatus
          conversationStatus={conversationStatus}
          isPausing={isPausing}
          handleStop={handleStopClick}
          handleResumeAgent={handleStartClick}
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
