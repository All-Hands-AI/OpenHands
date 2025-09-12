import React from "react";
import { useNavigate } from "react-router";
import { useDispatch } from "react-redux";

import { useConversationId } from "#/hooks/use-conversation-id";
import { clearTerminal } from "#/state/command-slice";
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
import { useStartConversation } from "#/hooks/mutation/use-start-conversation";
import { ConversationSubscriptionsProvider } from "#/context/conversation-subscriptions-provider";
import { useUserProviders } from "#/hooks/use-user-providers";

import { ConversationMain } from "#/components/features/conversation/conversation-main";
import { ConversationName } from "#/components/features/conversation/conversation-name";

import { ConversationTabs } from "#/components/features/conversation/conversation-tabs/conversation-tabs";
import { useWSErrorMessage } from "#/hooks/use-ws-error-message";

function AppContent() {
  useConversationConfig();

  const { conversationId } = useConversationId();
  const { data: conversation, isFetched } = useActiveConversation();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();
  const startConversation = useStartConversation();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { removeErrorMessage } = useWSErrorMessage();

  // Track if we've processed the initial conversation state to avoid auto-restarting user-stopped conversations
  const hasProcessedInitialState = React.useRef(false);

  // Fetch batch feedback data when conversation is loaded
  useBatchFeedback();

  // Set the document title to the conversation title when available
  useDocumentTitleFromState();

  React.useEffect(() => {
    if (isFetched && !conversation && isAuthed) {
      displayErrorToast(
        "This conversation does not exist, or you do not have permission to access it.",
      );
      navigate("/");
    } else if (
      conversation?.status === "STOPPED" &&
      !hasProcessedInitialState.current
    ) {
      // Only start the conversation if the state is stopped on initial load
      // This prevents auto-restarting when user manually stops the conversation
      hasProcessedInitialState.current = true;
      startConversation.mutate(
        {
          conversationId: conversation.conversation_id,
          providers,
        },
        {
          onSuccess: removeErrorMessage,
        },
      );
    } else if (conversation && !hasProcessedInitialState.current) {
      // Mark as processed if we have a conversation in any other state
      hasProcessedInitialState.current = true;
    }
  }, [
    conversation?.conversation_id,
    conversation?.status,
    isFetched,
    isAuthed,
    providers,
  ]);

  React.useEffect(() => {
    dispatch(clearTerminal());
    dispatch(clearJupyter());
    dispatch(resetConversationState());
    dispatch(setCurrentAgentState(AgentState.LOADING));
    // Reset the initial state tracking when navigating to a different conversation
    hasProcessedInitialState.current = false;
  }, [conversationId]);

  useEffectOnce(() => {
    dispatch(clearTerminal());
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
