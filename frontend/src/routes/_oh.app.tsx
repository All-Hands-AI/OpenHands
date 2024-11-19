import { useDisclosure } from "@nextui-org/react";
import React from "react";
import {
  Outlet,
  useLoaderData,
  json,
  ClientActionFunctionArgs,
} from "@remix-run/react";
import { useDispatch } from "react-redux";
import { useQuery } from "@tanstack/react-query";
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
import { isGitHubErrorReponse, retrieveLatestGitHubCommit } from "#/api/github";
import { clearJupyter } from "#/state/jupyterSlice";
import { FilesProvider } from "#/context/files";
import { ChatInterface } from "#/components/chat-interface";
import { WsClientProvider } from "#/context/ws-client-provider";
import { EventHandler } from "#/components/event-handler";

export const clientLoader = async () => {
  const ghToken = localStorage.getItem("ghToken");
  const repo =
    store.getState().initalQuery.selectedRepository ||
    localStorage.getItem("repo");

  const settings = getSettings();
  const token = localStorage.getItem("token");

  if (repo) localStorage.setItem("repo", repo);

  return json({
    settings,
    token,
    ghToken,
    repo,
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
  const { settings, token, ghToken, repo } =
    useLoaderData<typeof clientLoader>();

  const { data: latestGitHubCommit } = useQuery({
    queryKey: ["latest_commit", ghToken, repo],
    queryFn: async () => {
      const data = await retrieveLatestGitHubCommit(ghToken!, repo!);
      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve latest commit");
      }

      return data[0];
    },
    enabled: !!ghToken && !!repo,
  });

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
