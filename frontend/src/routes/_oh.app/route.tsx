import { useDisclosure } from "@nextui-org/react";
import React from "react";
import { Outlet } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import {
  ConversationProvider,
  useConversation,
} from "#/context/conversation-context";
import { Controls } from "#/components/features/controls/controls";
import { RootState } from "#/store";
import { clearMessages } from "#/state/chat-slice";
import { clearTerminal } from "#/state/command-slice";
import { useEffectOnce } from "#/hooks/use-effect-once";
import CodeIcon from "#/icons/code.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ListIcon from "#/icons/list-type-number.svg?react";
import { clearJupyter } from "#/state/jupyter-slice";
import { FilesProvider } from "#/context/files";
import { ChatInterface } from "../../components/features/chat/chat-interface";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "./event-handler";
import { useLatestRepoCommit } from "#/hooks/query/use-latest-repo-commit";
import { useAuth } from "#/context/auth-context";
import { useSettings } from "#/context/settings-context";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";
import { Container } from "#/components/layout/container";
import Security from "#/components/shared/modals/security/security";
import { CountBadge } from "#/components/layout/count-badge";
import { TerminalStatusLabel } from "#/components/features/terminal/terminal-status-label";
import styles from "./panels.module.css";

function AppContent() {
  const { gitHubToken } = useAuth();
  const { settings } = useSettings();
  const { conversationId } = useConversation();

  const dispatch = useDispatch();
  useConversationConfig();

  const { selectedRepository } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const { updateCount } = useSelector((state: RootState) => state.browser);

  const { data: latestGitHubCommit } = useLatestRepoCommit({
    repository: selectedRepository,
  });

  useEffectOnce(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  });

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  return (
    <WsClientProvider ghToken={gitHubToken} conversationId={conversationId}>
      <EventHandler>
        <div className="flex flex-col h-full gap-3">
          <div className="flex h-full overflow-auto">
            <PanelGroup direction="horizontal" className="w-full">
              <Panel defaultSize={25} minSize={15} maxSize={50} collapsible>
                <Container className="h-full relative">
                  <ChatInterface />
                </Container>
              </Panel>

              <PanelResizeHandle className={styles.resizeHandle}>
                <div className={styles.resizeHandleBar} />
              </PanelResizeHandle>

              <Panel className="hidden md:block">
                <Container
                  className="h-full"
                  labels={[
                    {
                      label: <TerminalStatusLabel />,
                      to: "",
                      icon: <CodeIcon />,
                    },
                    { label: "Workspace", to: "workspace", icon: <CodeIcon /> },
                    { label: "Jupyter", to: "jupyter", icon: <ListIcon /> },
                    {
                      label: (
                        <div className="flex items-center gap-1">
                          Browser
                          {updateCount > 0 && (
                            <CountBadge count={updateCount} />
                          )}
                        </div>
                      ),
                      to: "browser",
                      icon: <GlobeIcon />,
                    },
                  ]}
                >
                  <FilesProvider>
                    {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
                     * that it loads only in the client-side. */}
                    <React.Suspense fallback={<div className="h-full" />}>
                      <Outlet />
                    </React.Suspense>
                  </FilesProvider>
                </Container>
              </Panel>
            </PanelGroup>
          </div>

          <div className="h-[60px]">
            <Controls
              setSecurityOpen={onSecurityModalOpen}
              showSecurityLock={!!settings.SECURITY_ANALYZER}
              lastCommitData={latestGitHubCommit || null}
            />
          </div>
          <Security
            isOpen={securityModalIsOpen}
            onOpenChange={onSecurityModalOpenChange}
            securityAnalyzer={settings.SECURITY_ANALYZER}
          />
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
