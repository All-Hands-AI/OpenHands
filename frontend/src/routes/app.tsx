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
import { Provider } from "react-redux";
import ChatInterface from "#/components/chat/ChatInterface";
import { getSettings } from "#/services/settings";
import Security from "../components/modals/security/Security";
import { Controls } from "#/components/controls";
import store from "#/store";
import { Container } from "#/components/container";
import ActionType from "#/types/ActionType";
import { handleAssistantMessage } from "#/services/actions";
import { addUserMessage } from "#/state/chatSlice";
import { useSocket } from "#/context/socket";
import { useEffectOnce } from "#/utils/use-effect-once";
import { sendTerminalCommand } from "#/services/terminalService";
import { appendInput, appendOutput } from "#/state/commandSlice";

const Terminal = React.lazy(() => import("../components/terminal/Terminal"));

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) => {
  const url = new URL(request.url);
  const q = url.searchParams.get("q");
  const repo = url.searchParams.get("repo");

  const settings = getSettings();
  const token = localStorage.getItem("token");
  const ghToken = localStorage.getItem("ghToken");

  return json({
    token,
    ghToken,
    repo,
    securityAnalyzer: settings.SECURITY_ANALYZER,
    q,
  });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const token = formData.get("token")?.toString();

  if (token) {
    localStorage.setItem("token", token);
  }

  return json(null);
};

function App() {
  const { start, stop, send } = useSocket();
  const { token, ghToken, repo, securityAnalyzer, q } =
    useLoaderData<typeof clientLoader>();
  const fetcher = useFetcher();

  useEffectOnce(() => {
    start({
      token,
      onOpen: () => {
        const settings = getSettings();
        const initEvent = {
          action: ActionType.INIT,
          args: settings,
        };

        send(JSON.stringify(initEvent));
        // first time connection, send the query if it exists
        if (!token) {
          if (q) {
            const event = {
              action: ActionType.MESSAGE,
              args: { content: q },
            };

            send(JSON.stringify(event));
            store.dispatch(addUserMessage({ content: q, imageUrls: [] }));
          }

          if (ghToken && repo) {
            // clone repo via terminal
            const url = `https://${ghToken}@github.com/${repo}.git`;
            const command = `git clone ${url}`;
            const event = sendTerminalCommand(command);

            send(event);
            store.dispatch(appendInput(command.replace(ghToken, "***")));
            store.dispatch(appendOutput(command.replace(ghToken, "***")));
          }
        }
      },
      onMessage: (message) => {
        console.warn("Received message", message);
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

    return () => stop();
  });

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  return (
    <Provider store={store}>
      <div data-testid="app" className="h-full flex flex-col gap-[10px]">
        <div className="h-full flex gap-3">
          <div className="w-1/4">
            <Container className="h-full" label="Chat">
              <ChatInterface />
            </Container>
          </div>

          <div className="flex flex-col gap-3 w-3/4">
            <Container
              className="h-full"
              labels={[
                { label: "Workspace", to: "" },
                { label: "Jupyter", to: "jupyter" },
                { label: "Browser (experimental)", to: "browser" },
              ]}
            >
              <Outlet />
            </Container>
            {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
             * that it loads only in the client-side. */}
            <Container className="h-2/5 min-h-0" label="Terminal">
              <React.Suspense fallback={<div className="h-full" />}>
                <Terminal />
              </React.Suspense>
            </Container>
          </div>
        </div>
        <Controls
          setSecurityOpen={onSecurityModalOpen}
          showSecurityLock={!!securityAnalyzer}
        />
        <Security
          isOpen={securityModalIsOpen}
          onOpenChange={onSecurityModalOpenChange}
          securityAnalyzer={securityAnalyzer}
        />
        <Toaster />
      </div>
    </Provider>
  );
}

export default App;
