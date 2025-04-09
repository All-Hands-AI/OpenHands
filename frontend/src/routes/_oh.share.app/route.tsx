import { ChatInterfaceShares } from "#/components/features/chat/chat-interface-shares";
import { Controls } from "#/components/features/controls/controls";
import { TerminalStatusLabel } from "#/components/features/terminal/terminal-status-label";
import { Container } from "#/components/layout/container";
import {
  Orientation,
  ResizablePanel,
} from "#/components/layout/resizable-panel";
import Security from "#/components/shared/modals/security/security";
import {
  ConversationProvider,
  useConversation,
} from "#/context/conversation-context";
import { FilesProvider } from "#/context/files";
import { useConversationConfig } from "#/hooks/query/use-conversation-config";
import { useSettings } from "#/hooks/query/use-settings";
import { useEffectOnce } from "#/hooks/use-effect-once";
import { I18nKey } from "#/i18n/declaration";
import CodeIcon from "#/icons/code.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import TerminalIcon from "#/icons/terminal.svg?react";
import { addUserMessage, clearMessages } from "#/state/chat-slice";
import { clearTerminal } from "#/state/command-slice";
import { clearFiles, clearInitialPrompt } from "#/state/initial-query-slice";
import { clearJupyter } from "#/state/jupyter-slice";
import { RootState } from "#/store";
import { useDisclosure } from "@heroui/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { Outlet } from "react-router";
import { ShareEventHandler } from "./event-handler";

function AppContent() {
  useConversationConfig();
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const { conversationId } = useConversation();
  // const { data: conversation, isFetched } = useUserConversation(
  //   conversationId || null,
  // );
  const { initialPrompt, files } = useSelector(
    (state: RootState) => state.initialQuery,
  );
  const dispatch = useDispatch();
  // const endSession = useEndSession();

  const [width, setWidth] = React.useState(window.innerWidth);

  // const Terminal = React.useMemo(
  //   () => React.lazy(() => import("#/components/features/terminal/terminal")),
  //   [],
  // );

  // React.useEffect(() => {
  //   if (isFetched && !conversation) {
  //     displayErrorToast(
  //       "This conversation does not exist, or you do not have permission to access it.",
  //     );
  //     endSession();
  //   }
  // }, [conversation, isFetched]);

  React.useEffect(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
    if (conversationId && (initialPrompt || files.length > 0)) {
      dispatch(
        addUserMessage({
          content: initialPrompt || "",
          imageUrls: files || [],
          timestamp: new Date().toISOString(),
          pending: true,
        }),
      );
      dispatch(clearInitialPrompt());
      dispatch(clearFiles());
    }
  }, [conversationId]);

  useEffectOnce(() => {
    dispatch(clearMessages());
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  });

  function handleResize() {
    setWidth(window.innerWidth);
  }

  React.useEffect(() => {
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  function renderMain() {
    if (width <= 640) {
      return (
        <div className="rounded-xl overflow-hidden border border-neutral-600 w-full">
          <ChatInterfaceShares />
        </div>
      );
    }
    return (
      <ResizablePanel
        orientation={Orientation.HORIZONTAL}
        className="grow h-full min-h-0 min-w-0"
        initialSize={550}
        firstClassName="rounded-xl overflow-hidden "
        secondClassName="flex flex-col overflow-hidden"
        firstChild={<ChatInterfaceShares />}
        secondChild={
          <Container
            className="h-full mt-4 rounded-xl !mb-4"
            labels={[
              {
                label: t(I18nKey.WORKSPACE$TITLE),
                to: "",
                icon: <CodeIcon />,
              },
              {
                label: <TerminalStatusLabel />,
                to: "terminal",
                icon: <TerminalIcon />,
              },
              {
                label: (
                  <div className="flex items-center gap-1">
                    {t(I18nKey.BROWSER$TITLE)}
                  </div>
                ),
                to: "browser",
                icon: <GlobeIcon />,
              },
            ]}
          >
            <div className="flex flex-col h-full">
              <FilesProvider>
                <Outlet />
              </FilesProvider>

              <Controls
                setSecurityOpen={onSecurityModalOpen}
                showSecurityLock={!!settings?.SECURITY_ANALYZER}
              />
            </div>
          </Container>
        }
      />
    );
  }

  return (
    <ShareEventHandler conversationId={conversationId}>
      <div data-testid="app-route" className="flex flex-col h-full gap-3">
        <div className="flex h-full overflow-auto">{renderMain()}</div>

        {settings && (
          <Security
            isOpen={securityModalIsOpen}
            onOpenChange={onSecurityModalOpenChange}
            securityAnalyzer={settings.SECURITY_ANALYZER}
          />
        )}
      </div>
    </ShareEventHandler>
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
