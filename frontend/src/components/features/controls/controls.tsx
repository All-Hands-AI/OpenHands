import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { ConversationCard } from "../conversation-panel/conversation-card";
import { setConversation } from "#/state/conversation-slice";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const dispatch = useDispatch();
  const { data: conversation } = useUserConversation();

  useEffect(() => {
    if (conversation) {
      dispatch(
        setConversation({
          id: conversation.conversation_id,
          status: conversation.status,
          selectedRepository: conversation.selected_repository,
          createdAt: conversation.created_at,
          lastUpdatedAt: conversation.last_updated_at,
        }),
      );
    }
  }, [conversation, dispatch]);

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
        showDisplayCostOption
        title={conversation?.title ?? ""}
        lastUpdatedAt={conversation?.created_at ?? ""}
        selectedRepository={conversation?.selected_repository ?? null}
        status={conversation?.status}
        conversationId={conversation?.conversation_id}
      />
    </div>
  );
}
