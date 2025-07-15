import { useDisclosure } from "@heroui/react";
import React from "react";
import { useNavigate } from "react-router";
import { useDispatch } from "react-redux";

import { useConversationId } from "#/hooks/use-conversation-id";
import { Controls } from "#/components/features/controls/controls";
import { clearTerminal } from "#/state/command-slice";
import { useEffectOnce } from "#/hooks/use-effect-once";
import { clearJupyter } from "#/state/jupyter-slice";

import { ChatInterface } from "../components/features/chat/chat-interface";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "../wrapper/event-handler";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";

import {
  Orientation,
  ResizablePanel,
} from "#/components/layout/resizable-panel";
import Security from "#/components/shared/modals/security/security";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useSettings } from "#/hooks/query/use-settings";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { ConversationSubscriptionsProvider } from "#/context/conversation-subscriptions-provider";
import { useUserProviders } from "#/hooks/use-user-providers";
import { ConversationTabs } from "#/components/features/conversation/conversation-tabs";

function AppContent() {
  useConversationConfig();
  const { data: settings } = useSettings();
  const { conversationId } = useConversationId();
  const { data: conversation, isFetched, refetch } = useActiveConversation();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();

  const dispatch = useDispatch();
  const navigate = useNavigate();

  // Set the document title to the conversation title when available
  useDocumentTitleFromState();

  const [width, setWidth] = React.useState(window.innerWidth);

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

  function handleResize() {
    setWidth(window.innerWidth);
  }

  React.useEffect(() => {
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  function renderMain() {
    if (width <= 1024) {
      return (
        <div className="flex flex-col gap-3 overflow-auto w-full">
          <div className="rounded-xl overflow-hidden border border-neutral-600 w-full bg-base-secondary min-h-[494px]">
            <ChatInterface />
          </div>
          <div className="h-full w-full min-h-[494px]">
            <ConversationTabs />
          </div>
        </div>
      );
    }
    return (
      <ResizablePanel
        orientation={Orientation.HORIZONTAL}
        className="grow h-full min-h-0 min-w-0"
        initialSize={500}
        firstClassName="rounded-xl overflow-hidden border border-neutral-600 bg-base-secondary"
        secondClassName="flex flex-col overflow-hidden"
        firstChild={<ChatInterface />}
        secondChild={<ConversationTabs />}
      />
    );
  }

  return (
    <WsClientProvider conversationId={conversationId}>
      <ConversationSubscriptionsProvider>
        <EventHandler>
          <div data-testid="app-route" className="flex flex-col h-full gap-3">
            <div className="flex h-full overflow-auto">{renderMain()}</div>

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
  );
}

function App() {
  return <AppContent />;
}

export default App;
