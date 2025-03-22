import { useParams } from "react-router";
import React from "react";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { ConversationCard } from "../conversation-panel/conversation-card";
import { useSelector } from "react-redux";
import { queryClient } from "#/entry.client";
import OpenHands from "#/api/open-hands";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

const defaultTitlePattern = /^Conversation [a-f0-9]+$/;

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const params = useParams();
  const { data: conversation } = useUserConversation(
    params.conversationId ?? null,
  );

  const [autogenerating, setAutogenerating] = React.useState(false);

  const autogenereateConversationTitle = async () => {
    await OpenHands.updateUserConversation(params.conversationId, { title: "" });

    // Invalidate the queries to refresh the data
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
    queryClient.invalidateQueries({
      queryKey: ["user", "conversations"],
    });
  }

  const { latestUserMessage } = useSelector((state: RootState) => state.latestUserMessage);
  React.useEffect(() => {
    if (!latestUserMessage || !conversation) {
      return;
    }
    if (conversation.title && !defaultTitlePattern.test(conversation.title)) {
      return;
    }
    if (autogenerating) {
      return;
    }
    setAutogenerating(true);
    autogenereateConversationTitle();
  }, [latestUserMessage, conversation]);


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
