import { useDisclosure } from "@nextui-org/react";
import React from "react";
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
import { CountBadge } from "#/components/layout/count-badge";

function App() {
  const { token, gitHubToken } = useAuth();
  const { settings } = useUserPrefs();
  const [leftPanelWidth, setLeftPanelWidth] = React.useState(50); // 50% default width
  const isDragging = React.useRef(false);

  const handleMouseDown = React.useCallback(() => {
    isDragging.current = true;
    document.body.style.userSelect = 'none';
  }, []);

  const handleMouseUp = React.useCallback(() => {
    isDragging.current = false;
    document.body.style.userSelect = '';
  }, []);

  const handleMouseMove = React.useCallback((e: MouseEvent) => {
    if (!isDragging.current) return;
    const containerWidth = window.innerWidth;
    const newWidth = (e.clientX / containerWidth) * 100;
    setLeftPanelWidth(Math.min(Math.max(20, newWidth), 80)); // Limit between 20% and 80%
  }, []);

  React.useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const dispatch = useDispatch();
  useConversationConfig();

  const { selectedRepository } = useSelector(
    (state: RootState) => state.initalQuery,
  );

  const { updateCount } = useSelector((state: RootState) => state.browser);

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
          <div className="flex h-full overflow-auto">
            <Container className="w-full md:w-auto max-h-full relative" style={{ width: `${leftPanelWidth}%` }}>
              <ChatInterface />
            </Container>

            <div 
              className="hidden md:block w-1 bg-default-100 hover:bg-default-200 cursor-col-resize" 
              onMouseDown={handleMouseDown}
            />

            <div className="hidden md:flex flex-col grow gap-3">
              <Container
                className="h-full"
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
                  { 
                    label: "Terminal",
                    to: "terminal",
                    icon: <CodeIcon />
                  }
                ]}
              >
                <FilesProvider>
                  <Outlet />
                </FilesProvider>
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

export default App;
