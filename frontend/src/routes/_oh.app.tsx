import { useDisclosure } from "@nextui-org/react";
import React from "react";
import {
  Outlet,
  useLoaderData,
  json,
  ClientActionFunctionArgs,
} from "@remix-run/react";
import { useDispatch } from "react-redux";
import { getSettings } from "#/services/settings";
import Security from "../components/modals/security/Security";
import { Controls } from "#/components/controls";
import store from "#/store";
import { Container } from "#/components/container";
import { clearMessages } from "#/state/chatSlice";
import { clearTerminal } from "#/state/commandSlice";
import { useEffectOnce } from "#/utils/use-effect-once";
import CodeIcon from "#/icons/code.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ListIcon from "#/icons/list-type-number.svg?react";
import { clearInitialQuery } from "#/state/initial-query-slice";
import { isGitHubErrorReponse, retrieveLatestGitHubCommit } from "#/api/github";
import { clearJupyter } from "#/state/jupyterSlice";
import { FilesProvider } from "#/context/files";
import { ChatInterface } from "#/components/chat-interface";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "#/components/event-handler";

export const clientLoader = async () => {
  const ghToken = localStorage.getItem("ghToken");

  const q = store.getState().initalQuery.initialQuery;
  const repo =
    store.getState().initalQuery.selectedRepository ||
    localStorage.getItem("repo");

  const settings = getSettings();
  const token = localStorage.getItem("token");

  if (repo) localStorage.setItem("repo", repo);

  let lastCommit: GitHubCommit | null = null;
  if (ghToken && repo) {
    const data = await retrieveLatestGitHubCommit(ghToken, repo);
    if (isGitHubErrorReponse(data)) {
      // TODO: Handle error
      console.error("Failed to retrieve latest commit", data);
    } else {
      [lastCommit] = data;
    }
  }

  return json({
    settings,
    token,
    ghToken,
    repo,
    q,
    lastCommit,
  });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();

  const token = formData.get("token")?.toString();
  const ghToken = formData.get("ghToken")?.toString();

  if (token) localStorage.setItem("token", token);
  if (ghToken) localStorage.setItem("ghToken", ghToken);

  return json(null);
};

function App() {
  const dispatch = useDispatch();
  const { settings, token, ghToken, lastCommit } =
    useLoaderData<typeof clientLoader>();

  const secrets = React.useMemo(
    () => [ghToken, token].filter((secret) => secret !== null),
    [ghToken, token],
  );

  const Terminal = React.useMemo(
    () => React.lazy(() => import("../components/terminal/Terminal")),
    [],
  );

  useEffectOnce(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
    dispatch(clearInitialQuery()); // Clear initial query when navigating to /app
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
      ghToken={ghToken}
      settings={settings}
    >
      <EventHandler>
        <div className="flex flex-col h-full gap-3">
          <div className="flex h-full overflow-auto gap-3">
            <Container className="w-[390px] max-h-full relative">
              <ChatInterface />
            </Container>

            <div className="flex flex-col grow gap-3">
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
          </div>

          <div className="h-[60px]">
            <Controls
              setSecurityOpen={onSecurityModalOpen}
              showSecurityLock={!!settings.SECURITY_ANALYZER}
              lastCommitData={lastCommit}
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
