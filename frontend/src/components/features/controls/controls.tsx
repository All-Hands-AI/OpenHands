import { useState } from "react";
import { SecurityLock } from "./security-lock";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { ConversationCard } from "../conversation-panel/conversation-card";
import { Provider } from "#/types/settings";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const { data: conversation } = useActiveConversation();
  const [contextMenuOpen, setContextMenuOpen] = useState(false);

  return (
    <div className="flex flex-col gap-2 md:items-center md:justify-between md:flex-row">
      <div className="flex items-center gap-2">
        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>

      <ConversationCard
        variant="compact"
        showOptions
        title={conversation?.title ?? ""}
        lastUpdatedAt={conversation?.created_at ?? ""}
        selectedRepository={{
          selected_repository: conversation?.selected_repository ?? null,
          selected_branch: conversation?.selected_branch ?? null,
          git_provider: (conversation?.git_provider as Provider) ?? null,
        }}
        conversationStatus={conversation?.status}
        conversationId={conversation?.conversation_id}
        contextMenuOpen={contextMenuOpen}
        onContextMenuToggle={setContextMenuOpen}
      />
    </div>
  );
}
