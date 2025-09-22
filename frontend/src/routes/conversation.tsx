import React from "react";
import { useNavigate } from "react-router";
import { useDispatch } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";

import { useConversationId } from "#/hooks/use-conversation-id";
import { useCommandStore } from "#/state/command-store";
import { useEffectOnce } from "#/hooks/use-effect-once";
import { clearJupyter } from "#/state/jupyter-slice";
import { resetConversationState } from "#/state/conversation-slice";
import { setCurrentAgentState } from "#/state/agent-slice";
import { AgentState } from "#/types/agent-state";

import { useBatchFeedback } from "#/hooks/query/use-batch-feedback";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "../wrapper/event-handler";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";

import { useActiveConversation } from "#/hooks/query/use-active-conversation";

import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { ConversationSubscriptionsProvider } from "#/context/conversation-subscriptions-provider";
import { useUserProviders } from "#/hooks/use-user-providers";

import { ConversationMain } from "#/components/features/conversation/conversation-main/conversation-main";
import { ConversationName } from "#/components/features/conversation/conversation-name";

import { ConversationTabs } from "#/components/features/conversation/conversation-tabs/conversation-tabs";
import { useStartConversation } from "#/hooks/mutation/use-start-conversation";

function AppContent() {
  useConversationConfig();

  const { conversationId } = useConversationId();
  const { data: conversation, isFetched, refetch } = useActiveConversation();
  const { mutate: startConversation } = useStartConversation();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const clearTerminal = useCommandStore((state) => state.clearTerminal);
  const queryClient = useQueryClient();

  // Fetch batch feedback data when conversation is loaded
  useBatchFeedback();

  // Set the document title to the conversation title when available
  useDocumentTitleFromState();

  // Force fresh conversation data when navigating to prevent stale cache issues
  React.useEffect(() => {
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
  }, [conversationId, queryClient]);

  React.useEffect(() => {
    if (isFetched && !conversation && isAuthed) {
      displayErrorToast(
        "This conversation does not exist, or you do not have permission to access it.",
      );
      navigate("/");
    } else if (conversation?.status === "STOPPED") {
      // If conversation is STOPPED, attempt to start it
      startConversation(
        { conversationId: conversation.conversation_id, providers },
        {
          onError: (error) => {
            displayErrorToast(`Failed to start conversation: ${error.message}`);
            // Refetch the conversation to ensure UI consistency
            refetch();
          },
        },
      );
    }
  }, [
    conversation?.conversation_id,
    conversation?.status,
    isFetched,
    isAuthed,
    providers,
  ]);

  React.useEffect(() => {
    clearTerminal();
    dispatch(clearJupyter());
    dispatch(resetConversationState());
    dispatch(setCurrentAgentState(AgentState.LOADING));
  }, [conversationId, clearTerminal]);

  useEffectOnce(() => {
    clearTerminal();
    dispatch(clearJupyter());
    dispatch(resetConversationState());
    dispatch(setCurrentAgentState(AgentState.LOADING));
  });

  return (
    <WsClientProvider conversationId={conversationId}>
      <ConversationSubscriptionsProvider>
        <EventHandler>
          <div
            data-testid="app-route"
            className="p-3 md:p-0 flex flex-col h-full gap-3"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4.5 pt-2 lg:pt-0">
              <ConversationName />
              <ConversationTabs />
            </div>

            <div className="flex h-full overflow-auto">
              <ConversationMain />
            </div>
          </div>
        </EventHandler>
      </ConversationSubscriptionsProvider>
    </WsClientProvider>
  );
}

function App() {
  return <AppContent />;
}

export default App;
