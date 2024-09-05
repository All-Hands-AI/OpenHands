import { useDisclosure } from "@nextui-org/react";
import React, { lazy, Suspense } from "react";
import { Toaster } from "react-hot-toast";
import { json, LoaderFunctionArgs } from "@remix-run/node";
import { Outlet, useLoaderData } from "@remix-run/react";
import { Provider } from "react-redux";
import ChatInterface from "#/components/chat/ChatInterface";
import LoadPreviousSessionModal from "#/components/modals/load-previous-session/LoadPreviousSessionModal";
import Session from "#/services/session";
import { getToken } from "#/services/auth";
import { DEFAULT_SETTINGS } from "#/services/settings";
import Security from "../components/modals/security/Security";
import { Controls } from "#/components/controls";
import { getSettingsSession } from "#/sessions";
import store from "#/store";
import { Container } from "#/components/container";

const Terminal = lazy(() => import("../components/terminal/Terminal"));

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSettingsSession(request.headers.get("Cookie"));
  const settings = session.get("settings") || DEFAULT_SETTINGS;

  return json({ securityAnalyzer: settings.SECURITY_ANALYZER });
};

function App() {
  const { securityAnalyzer } = useLoaderData<typeof loader>();

  const {
    isOpen: loadPreviousSessionModalIsOpen,
    onOpen: onLoadPreviousSessionModalOpen,
    onOpenChange: onLoadPreviousSessionModalOpenChange,
  } = useDisclosure();

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  React.useEffect(() => {
    if (getToken()) {
      onLoadPreviousSessionModalOpen();
    } else {
      Session.startNewSession();
    }
  }, []);

  return (
    <Provider store={store}>
      <div className="h-full flex flex-col gap-[10px]">
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
              <Suspense fallback={<div className="h-full" />}>
                <Terminal />
              </Suspense>
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
        <LoadPreviousSessionModal
          isOpen={loadPreviousSessionModalIsOpen}
          onOpenChange={onLoadPreviousSessionModalOpenChange}
        />
        <Toaster />
      </div>
    </Provider>
  );
}

export default App;
