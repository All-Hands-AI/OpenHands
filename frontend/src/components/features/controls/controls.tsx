import { useParams } from "react-router";
import React from "react";
import { useSelector } from "react-redux";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { ConversationCard } from "../conversation-panel/conversation-card";
import { queryClient } from "#/entry.client";
import OpenHands from "#/api/open-hands";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

const defaultTitlePattern = /^Conversation [a-f0-9]+$/;

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const params = useParams();
  const { data: conversation, isFetched } = useUserConversation(
    params.conversationId ?? null,
  );

  const [autogenerating, setAutogenerating] = React.useState(false);

  const autogenereateConversationTitle = async () => {
    console.log("Autogenerating conversation title...");
    await OpenHands.updateUserConversation(params.conversationId, {
      title: "",
    });

    /*
    queryClient.setQueryData(
      ["user", "conversation", params.conversationId],
      (oldData) => oldData ? { ...oldData, title: "gotcha" } : oldData
    );
    */
  };

  const { latestUserMessage } = useSelector(
    (state: RootState) => state.latestUserMessage,
  );
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
    setTimeout(() => {
      // FIXME: Sometimes the message isn't quite ready on the backend
      autogenereateConversationTitle();
    }, 1000);
  }, [latestUserMessage, conversation]);

  React.useEffect(() => {
    if (isFetched && !conversation) {
      displayErrorToast(
        "This conversation does not exist, or you do not have permission to access it.",
      );
      endSession();
    }
  }, [conversation, isFetched]);


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
