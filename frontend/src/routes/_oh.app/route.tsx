import { useDisclosure } from "@nextui-org/react";
import React from "react";
import { Outlet } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import toast from "react-hot-toast";
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
import { useEndSession } from "#/hooks/use-end-session";
import { useUserConversation } from "#/hooks/query/get-conversation-permissions";
import { CountBadge } from "#/components/layout/count-badge";
import { TerminalStatusLabel } from "#/components/features/terminal/terminal-status-label";
import { MULTI_CONVO_UI_IS_ENABLED } from "#/utils/constants";

function AppContent() {
  const { gitHubToken } = useAuth();
  const endSession = useEndSession();

  const { settings } = useSettings();
  const { conversationId } = useConversation();

  const dispatch = useDispatch();

  useConversationConfig();
  const { data: conversation, isFetched } = useUserConversation(
    conversationId || null,
  );

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

  React.useEffect(() => {
    if (MULTI_CONVO_UI_IS_ENABLED && isFetched && !conversation) {
      toast.error(
        "This conversation does not exist, or you do not have permission to access it.",
      );
      endSession();
    }
  }, [conversation, isFetched]);

  React.useEffect(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  }, [conversationId]);

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
        <div data-testid="app-route" className="flex flex-col h-full gap-3">
          <div className="flex h-full overflow-auto gap-3">
            <Container className="w-full md:w-[390px] max-h-full relative">
              <ChatInterface />
            </Container>

            <div className="hidden md:flex flex-col grow gap-3">
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
