import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { Tools } from "../../controls/tools";
import { useUnifiedPauseConversationSandbox } from "#/hooks/mutation/use-unified-stop-conversation";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useUnifiedResumeConversationSandbox } from "#/hooks/mutation/use-unified-start-conversation";
import { useUserProviders } from "#/hooks/use-user-providers";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useSendMessage } from "#/hooks/use-send-message";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { AgentState } from "#/types/agent-state";
import { useV1PauseConversation } from "#/hooks/mutation/use-v1-pause-conversation";
import { useV1ResumeConversation } from "#/hooks/mutation/use-v1-resume-conversation";

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
  const { data: conversation } = useActiveConversation();
  const pauseConversationSandboxMutation = useUnifiedPauseConversationSandbox();
  const resumeConversationSandboxMutation =
    useUnifiedResumeConversationSandbox();
  const v1PauseConversationMutation = useV1PauseConversation();
  const v1ResumeConversationMutation = useV1ResumeConversation();
  const { conversationId } = useConversationId();
  const { providers } = useUserProviders();
  const { send } = useSendMessage();

  const isV1Conversation = conversation?.conversation_version === "V1";

  const handleStopClick = () => {
    pauseConversationSandboxMutation.mutate({ conversationId });
  };

  const handlePauseAgent = () => {
    if (isV1Conversation) {
      // V1: Pause the conversation (agent execution)
      v1PauseConversationMutation.mutate({ conversationId });
      return;
    }

    // V0: Send agent state change event to stop the agent
    send(generateAgentStateChangeEvent(AgentState.STOPPED));
  };

  const handleResumeAgentClick = () => {
    if (isV1Conversation) {
      // V1: Resume the conversation (agent execution)
      v1ResumeConversationMutation.mutate({ conversationId });
      return;
    }

    // V0: Call the original handleResumeAgent (sends "continue" message)
    handleResumeAgent();
  };

  const handleStartClick = () => {
    resumeConversationSandboxMutation.mutate({ conversationId, providers });
  };

  const isPausing =
    pauseConversationSandboxMutation.isPending ||
    v1PauseConversationMutation.isPending;

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
        handleStop={handlePauseAgent}
        handleResumeAgent={handleResumeAgentClick}
        disabled={disabled}
        isPausing={isPausing}
      />
    </div>
  );
}
