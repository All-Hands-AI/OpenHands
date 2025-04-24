import { useDisclosure } from "@heroui/react";
import React from "react";
import { Outlet } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { FaServer, FaExternalLinkAlt } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { DiGit } from "react-icons/di";
import { VscCode } from "react-icons/vsc";
import { I18nKey } from "#/i18n/declaration";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import {
  ConversationProvider,
  useConversation,
} from "#/context/conversation-context";
import { Controls } from "#/components/features/controls/controls";
import { clearMessages, addUserMessage } from "#/state/chat-slice";
import { clearTerminal } from "#/state/command-slice";
import { useEffectOnce } from "#/hooks/use-effect-once";

import GlobeIcon from "#/icons/globe.svg?react";
import JupyterIcon from "#/icons/jupyter.svg?react";
import TerminalIcon from "#/icons/terminal.svg?react";
import { clearJupyter } from "#/state/jupyter-slice";

import { ChatInterface } from "../components/features/chat/chat-interface";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "../wrapper/event-handler";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";
import { Container } from "#/components/layout/container";
import {
  Orientation,
  ResizablePanel,
} from "#/components/layout/resizable-panel";
import Security from "#/components/shared/modals/security/security";
import { useEndSession } from "#/hooks/use-end-session";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { ServedAppLabel } from "#/components/layout/served-app-label";
import { useSettings } from "#/hooks/query/use-settings";
import { clearFiles, clearInitialPrompt } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state";

function AppContent() {
  useConversationConfig();
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const { conversationId } = useConversation();
  const { data: conversation, isFetched } = useUserConversation(
    conversationId || null,
  );
  const { initialPrompt, files } = useSelector(
    (state: RootState) => state.initialQuery,
  );
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const dispatch = useDispatch();
  const endSession = useEndSession();

  // Set the document title to the conversation title when available
  useDocumentTitleFromState();

  const [width, setWidth] = React.useState(window.innerWidth);

  React.useEffect(() => {
    if (isFetched && !conversation) {
      displayErrorToast(
        "This conversation does not exist, or you do not have permission to access it.",
      );
      endSession();
    }
  }, [conversation, isFetched]);

  React.useEffect(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
    if (conversationId && (initialPrompt || files.length > 0)) {
      dispatch(
        addUserMessage({
          content: initialPrompt || "",
          imageUrls: files || [],
          timestamp: new Date().toISOString(),
          pending: true,
        }),
      );
      dispatch(clearInitialPrompt());
      dispatch(clearFiles());
    }
  }, [conversationId]);

  useEffectOnce(() => {
    dispatch(clearMessages());
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
    if (width <= 640) {
      return (
        <div className="rounded-xl overflow-hidden border border-neutral-600 w-full bg-base-secondary">
          <ChatInterface />
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
        secondChild={
          <Container
            className="h-full w-full"
            labels={[
              {
                label: "Changes",
                to: "",
                icon: <DiGit className="w-6 h-6" />,
              },
              {
                label: (
                  <div className="flex items-center gap-1">
                    {t(I18nKey.VSCODE$TITLE)}
                  </div>
                ),
                to: "vscode",
                icon: <VscCode className="w-5 h-5" />,
                rightContent: !RUNTIME_INACTIVE_STATES.includes(
                  curAgentState,
                ) ? (
                  <FaExternalLinkAlt
                    className="w-3 h-3 text-neutral-400 cursor-pointer"
                    onClick={async (e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      if (conversationId) {
                        try {
                          const response = await fetch(
                            `/api/conversations/${conversationId}/vscode-url`,
                          );
                          const data = await response.json();
                          if (data.vscode_url) {
                            window.open(data.vscode_url, "_blank");
                          }
                        } catch (err) {
                          // Silently handle the error
                        }
                      }
                    }}
                  />
                ) : null,
              },
              {
                label: t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL),
                to: "terminal",
                icon: <TerminalIcon />,
              },
              { label: "Jupyter", to: "jupyter", icon: <JupyterIcon /> },
              {
                label: <ServedAppLabel />,
                to: "served",
                icon: <FaServer />,
              },
              {
                label: (
                  <div className="flex items-center gap-1">
                    {t(I18nKey.BROWSER$TITLE)}
                  </div>
                ),
                to: "browser",
                icon: <GlobeIcon />,
              },
            ]}
          >
            <Outlet />
          </Container>
        }
      />
    );
  }

  return (
    <WsClientProvider conversationId={conversationId}>
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
    </WsClientProvider>
  );
}

function App() {
  return (
    <ConversationProvider>
      <AppContent />
    </ConversationProvider>
  );
}

export default App;
