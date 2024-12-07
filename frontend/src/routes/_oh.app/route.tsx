import { useDisclosure } from "@nextui-org/react";
import React from "react";
import clsx from "clsx";
import { Outlet } from "react-router";
import { useDispatch, useSelector } from "react-redux";
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
import { useUserPrefs } from "#/context/user-prefs-context";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";
import { Container } from "#/components/layout/container";
import Security from "#/components/shared/modals/security/security";
import { CollapsePanelButton } from "#/components/shared/buttons/collapse-panel-button";

function App() {
  const { token, gitHubToken } = useAuth();
  const { settings } = useUserPrefs();
  const [isRightPanelCollapsed, setIsRightPanelCollapsed] = React.useState(false);

  const dispatch = useDispatch();
  useConversationConfig();

  const { selectedRepository } = useSelector(
    (state: RootState) => state.initalQuery,
  );

  const { data: latestGitHubCommit } = useLatestRepoCommit({
    repository: selectedRepository,
  });

  const secrets = React.useMemo(
    () => [gitHubToken, token].filter((secret) => secret !== null),
    [gitHubToken, token],
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

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  return (
    <WsClientProvider
      enabled
      token={token}
      ghToken={gitHubToken}
      selectedRepository={selectedRepository}
      settings={settings}
    >
      <EventHandler>
        <div className="flex flex-col h-full gap-3">
          <div className="flex h-full overflow-auto gap-3">
            <Container
              role="main"
              data-testid="chat-panel"
              className={clsx(
                "max-h-full relative transition-all duration-300",
                isRightPanelCollapsed ? "w-full" : "w-[390px]"
              )}
            >
              <ChatInterface />
            </Container>

            <div
              role="complementary"
              className={clsx(
                "flex flex-col gap-3 transition-all duration-300",
                isRightPanelCollapsed
                  ? "w-0 opacity-0 overflow-hidden"
                  : "grow opacity-100",
              )}>
              <Container
                className="h-2/3"
                labels={[
                  { label: "Workspace", to: "", icon: <CodeIcon /> },
                  { label: "Jupyter", to: "jupyter", icon: <ListIcon /> },
                  {
                    label: "Browser",
                    to: "browser",
                    icon: <GlobeIcon />,
                    isBeta: true,
                  },
                ]}
              >
                <FilesProvider>
                  <Outlet />
                </FilesProvider>
              </Container>
              {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
               * that it loads only in the client-side. */}
              <Container className="h-1/3 overflow-scroll" label="Terminal">
                <React.Suspense fallback={<div className="h-full" />}>
                  <Terminal secrets={secrets} />
                </React.Suspense>
              </Container>
            </div>

            <CollapsePanelButton
              isCollapsed={isRightPanelCollapsed}
              onClick={() => setIsRightPanelCollapsed((prev) => !prev)}
            />
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

export default App;
