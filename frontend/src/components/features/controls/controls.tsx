import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useAutoTitle } from "#/hooks/use-auto-title";
import { useParams } from "react-router";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const params = useParams();
  const { data: conversation } = useUserConversation(
    params.conversationId ?? null,
  );
  useAutoTitle();

  return (
    <div className="flex items-center justify-between flex-wrap gap-2 p-4 bg-[#000000] border-t border-gray-200">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />

        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>

      {/* <ConversationCard
        variant="compact"
        showOptions
        title={conversation?.title ?? ""}
        lastUpdatedAt={conversation?.created_at ?? ""}
        selectedRepository={conversation?.selected_repository ?? null}
        status={conversation?.status}
        conversationId={conversation?.conversation_id}
      /> */}
    </div>
  );
}
