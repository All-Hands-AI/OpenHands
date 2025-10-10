import { ConversationStatus } from "#/types/conversation-status";
import { ServerStatus } from "#/components/features/controls/server-status";
import { AgentStatus } from "#/components/features/controls/agent-status";
import { Tools } from "../../controls/tools";
import { SetupStatusIndicator } from "./setup-status-indicator";
import { useConversationSetupStore } from "#/stores/conversation-setup-store";

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
  // Get setup state from store
  const { isSetupMode, currentTask } = useConversationSetupStore();
  return (
    <div className="w-full space-y-2">
      {/* Setup status indicator - shows above the normal controls when in setup mode */}
      <SetupStatusIndicator task={currentTask} isActive={isSetupMode} />

      {/* Normal controls */}
      <div className="w-full flex items-center justify-between">
        <div className="flex items-center gap-1">
          <Tools />
          <ServerStatus conversationStatus={conversationStatus} />
        </div>
        <AgentStatus
          className="ml-2 md:ml-3"
          handleStop={() => handleStop(onStop)}
          handleResumeAgent={handleResumeAgent}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
