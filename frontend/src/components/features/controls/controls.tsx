import { useParams } from "react-router";
import React from "react";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { ConversationCard } from "../conversation-panel/conversation-card";
import { useAutoTitle } from "#/hooks/use-auto-title";

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
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />

        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>

      <ConversationCard
        variant="compact"
        showOptions
        title={conversation?.title ?? ""}
        lastUpdatedAt={conversation?.created_at ?? ""}
        selectedRepository={conversation?.selected_repository ?? null}
        status={conversation?.status}
        conversationId={conversation?.conversation_id}
        // Pass metrics data
        accumulated_cost={conversation?.accumulated_cost ?? 0}
        prompt_tokens={conversation?.prompt_tokens ?? 0}
        completion_tokens={conversation?.completion_tokens ?? 0}
        total_tokens={conversation?.total_tokens ?? 0}
      />
    </div>
  );
}
