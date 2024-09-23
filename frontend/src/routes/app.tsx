import { useDisclosure } from "@nextui-org/react";
import React from "react";
import { Toaster } from "react-hot-toast";
import {
  Outlet,
  useFetcher,
  useLoaderData,
  json,
  ClientActionFunctionArgs,
  ClientLoaderFunctionArgs,
} from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import ChatInterface from "#/components/chat/ChatInterface";
import { getSettings } from "#/services/settings";
import Security from "../components/modals/security/Security";
import { Controls } from "#/components/controls";
import { RootState } from "#/store";
import { Container } from "#/components/container";
import ActionType from "#/types/ActionType";
import { handleAssistantMessage } from "#/services/actions";
import { addUserMessage, clearMessages } from "#/state/chatSlice";
import { useSocket } from "#/context/socket";
import { sendTerminalCommand } from "#/services/terminalService";
import { appendInput } from "#/state/commandSlice";
import { useEffectOnce } from "#/utils/use-effect-once";
import CodeIcon from "#/assets/code.svg?react";
import GlobeIcon from "#/assets/globe.svg?react";
import ListIcon from "#/assets/list-type-number.svg?react";
import { createChatMessage } from "#/services/chatService";
import { clearFiles } from "#/state/selected-files-slice";

const Terminal = React.lazy(() => import("../components/terminal/Terminal"));

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) => {
  const url = new URL(request.url);
  const q = url.searchParams.get("q");
  const repo = url.searchParams.get("repo") || localStorage.getItem("repo");

  const settings = getSettings();
  const token = localStorage.getItem("token");
  const ghToken = localStorage.getItem("ghToken");

  if (repo) localStorage.setItem("repo", repo);

  return json({
    settings,
    token,
    ghToken,
    repo,
    q,
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
  const { files } = useSelector((state: RootState) => state.selectedFiles);
  const { start, send } = useSocket();
  const { settings, token, ghToken, repo, q } =
    useLoaderData<typeof clientLoader>();
  const fetcher = useFetcher();

  const startSocketConnection = React.useCallback(() => {
    start({
      token,
      onOpen: () => {
        const initEvent = {
          action: ActionType.INIT,
          args: settings,
        };
        send(JSON.stringify(initEvent));

        // first time connection
        if (!token) {
          if (ghToken) {
            const command = `export GH_TOKEN=${ghToken}`;
            const event = sendTerminalCommand(command);

            send(event);
            dispatch(appendInput(command.replace(ghToken, "***")));
          }

          if (ghToken && repo) {
            // clone repo via terminal
            const url = `https://${ghToken}@github.com/${repo}.git`;
            const command = `git clone ${url}`;
            const event = sendTerminalCommand(command);

            send(event);
            dispatch(appendInput(command.replace(ghToken, "***")));
          }

          // send the initial user query if it exists
          if (q) {
            const timestamp = new Date().toISOString();
            send(createChatMessage(q, files, timestamp));
            dispatch(
              addUserMessage({
                content: q,
                imageUrls: files,
                timestamp,
              }),
            );
            dispatch(clearFiles());
          }
        }
      },
      onMessage: (message) => {
        console.warn(
          "Received message",
          JSON.stringify(JSON.parse(message.data.toString()), null, 2),
        );
        // set token received from the server
        const parsed = JSON.parse(message.data.toString());
        if ("token" in parsed) {
          fetcher.submit({ token: parsed.token }, { method: "post" });
          return;
        }

        handleAssistantMessage(message.data.toString());
      },
      onClose: (event) => {
        console.warn("SOCKET CLOSED", event);
      },
      onError: (event) => {
        console.error("SOCKET ERROR", event);
      },
    });
  }, [token, q, ghToken, repo]);

  useEffectOnce(() => {
    // clear and restart the socket connection
    dispatch(clearMessages());
    startSocketConnection();
  });

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex h-full overflow-auto gap-3">
        <Container className="w-1/4 max-h-full" label="Chat">
          <ChatInterface />
        </Container>

        <div className="flex flex-col w-3/4 gap-3">
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
            <Outlet />
          </Container>
          {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
           * that it loads only in the client-side. */}
          <Container className="h-1/3 overflow-scroll" label="Terminal">
            <React.Suspense fallback={<div className="h-full" />}>
              <Terminal />
            </React.Suspense>
          </Container>
        </div>
      </div>

      <div className="h-[60px]">
        <Controls
          setSecurityOpen={onSecurityModalOpen}
          showSecurityLock={!!settings.SECURITY_ANALYZER}
        />
      </div>
      <Security
        isOpen={securityModalIsOpen}
        onOpenChange={onSecurityModalOpenChange}
        securityAnalyzer={settings.SECURITY_ANALYZER}
      />
      <Toaster />
    </div>
  );
}

export default App;
