import { useDisclosure } from "@heroui/react";
import React from "react";
import { useNavigate } from "react-router";
import { useDispatch, useSelector } from "react-redux";

import { useConversationId } from "#/hooks/use-conversation-id";
import { clearTerminal } from "#/state/command-slice";
import { useEffectOnce } from "#/hooks/use-effect-once";
import { clearJupyter } from "#/state/jupyter-slice";
import { RootState } from "#/store";

import { useBatchFeedback } from "#/hooks/query/use-batch-feedback";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "../wrapper/event-handler";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";

import Security from "#/components/shared/modals/security/security";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useSettings } from "#/hooks/query/use-settings";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { ConversationSubscriptionsProvider } from "#/context/conversation-subscriptions-provider";
import { useUserProviders } from "#/hooks/use-user-providers";
import { ChatActions } from "#/components/features/chat/chat-actions";
import { ConversationMain } from "#/components/features/conversation/conversation-main";
import { ConversationName } from "#/components/features/conversation/conversation-name";
import { Controls } from "#/components/features/controls/controls";
import { ConversationTabProvider } from "#/components/features/conversation/conversation-tabs/use-conversation-tabs";
import { ConversationTabs } from "#/components/features/conversation/conversation-tabs/conversation-tabs";

function AppContent() {
  useConversationConfig();
  const { data: settings } = useSettings();
  const { conversationId } = useConversationId();
  const { data: conversation, isFetched, refetch } = useActiveConversation();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

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
    } else if (conversation?.status === "STOPPED") {
      // start the conversation if the state is stopped on initial load
      OpenHands.startConversation(conversation.conversation_id, providers).then(
        () => refetch(),
      );
    }
  }, [conversation?.conversation_id, isFetched, isAuthed, providers]);

  React.useEffect(() => {
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  }, [conversationId]);

  useEffectOnce(() => {
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  });

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  return (
    <ConversationTabProvider>
      <WsClientProvider conversationId={conversationId}>
        <ConversationSubscriptionsProvider>
          <EventHandler>
            <div data-testid="app-route" className="flex flex-col h-full gap-3">
              <div className="flex items-center justify-between gap-4.5">
                <ConversationName />
                {isRightPanelShown && (
                  <>
                    <ConversationTabs />
                    <div className="h-full w-0.25 bg-[#525252]" />
                  </>
                )}
                <ChatActions />
              </div>

              <div className="flex h-full overflow-auto">
                <ConversationMain />
              </div>

              <Controls
                setSecurityOpen={onSecurityModalOpen}
                showSecurityLock={!!settings?.SECURITY_ANALYZER}
              />
              {settings && (
                <Security
                  isOpen={securityModalIsOpen}
                  onOpenChange={onSecurityModalOpenChange}
                  securityAnalyzer={settings.SECURITY_ANALYZER}
                />
              )}
            </div>
          </EventHandler>
        </ConversationSubscriptionsProvider>
      </WsClientProvider>
    </ConversationTabProvider>
  );
}

function App() {
  return <AppContent />;
}

export default App;
