import { useDisclosure } from "@nextui-org/react";
import React from "react";
import { Outlet } from "react-router";
import { useDispatch, useSelector } from "react-redux";
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
import { ToggleWorkspaceIconButton } from "#/components/shared/buttons/toggle-workspace-icon-button";

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

  const secrets = React.useMemo(
    () => [gitHubToken].filter((secret) => secret !== null),
    [gitHubToken],
  );

  const Terminal = React.useMemo(
    () => React.lazy(() => import("#/components/features/terminal/terminal")),
    [],
  );

  useEffectOnce(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  });

  const [isWorkspaceHidden, setIsWorkspaceHidden] = React.useState(false);

  const toggleWorkspace = React.useCallback(() => {
    setIsWorkspaceHidden((prev) => !prev);
  }, []);

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  return (
    <WsClientProvider ghToken={gitHubToken} conversationId={conversationId}>
      <EventHandler>
        <div className="flex flex-col h-full gap-3">
          <div className="flex h-full overflow-auto gap-3">
            <Container className={`w-full ${isWorkspaceHidden ? "" : "md:w-[390px]"} max-h-full`}>
              <ChatInterface />
            </Container>

            <div className={`hidden md:flex flex-col grow gap-3 transition-all duration-300 relative ${isWorkspaceHidden ? "w-0 opacity-0 overflow-hidden" : ""}`}>
              <div className="absolute right-0 top-1/2 -translate-y-1/2 z-10">
                <ToggleWorkspaceIconButton onClick={toggleWorkspace} isHidden={isWorkspaceHidden} />
              </div>
              <Container
                className="h-2/3"
                labels={[
                  { label: "Workspace", to: "", icon: <CodeIcon /> },
                  { label: "Jupyter", to: "jupyter", icon: <ListIcon /> },
                  {
                    label: (
                      <div className="flex items-center gap-1">
                        Browser
                        {updateCount > 0 && <CountBadge count={updateCount} />}
                      </div>
                    ),
                    to: "browser",
                    icon: <GlobeIcon />,
                  },
                ]}
              >
                <FilesProvider>
                  <Outlet />
                </FilesProvider>
              </Container>
              {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
               * that it loads only in the client-side. */}
              <Container
                className="h-1/3 overflow-scroll"
                label={<TerminalStatusLabel />}
              >
                <React.Suspense fallback={<div className="h-full" />}>
                  <Terminal secrets={secrets} />
                </React.Suspense>
              </Container>
            </div>
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
