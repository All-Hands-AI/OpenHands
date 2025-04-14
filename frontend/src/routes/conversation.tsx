import { ChatInterface } from "#/components/features/chat/chat-interface"
import { Container } from "#/components/layout/container"
import {
  Orientation,
  ResizablePanel,
} from "#/components/layout/resizable-panel"
import ThesisComputer from "#/components/layout/RightSideContent"
import ViewFile from "#/components/layout/view-file"
import {
  ConversationProvider,
  useConversation,
} from "#/context/conversation-context"
import { FilesProvider } from "#/context/files"
import { WsClientProvider } from "#/context/ws-client-provider"
import { useConversationConfig } from "#/hooks/query/use-conversation-config"
import { useSettings } from "#/hooks/query/use-settings"
import { useUserConversation } from "#/hooks/query/use-user-conversation"
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state"
import { useEffectOnce } from "#/hooks/use-effect-once"
import { useEndSession } from "#/hooks/use-end-session"
import { addUserMessage, clearMessages } from "#/state/chat-slice"
import { clearTerminal } from "#/state/command-slice"
import { clearComputerList } from "#/state/computer-slice"
import { clearFiles, clearInitialPrompt } from "#/state/initial-query-slice"
import { clearJupyter } from "#/state/jupyter-slice"
import { RootState } from "#/store"
import { displayErrorToast } from "#/utils/custom-toast-handlers"
import { EventHandler } from "#/wrapper/event-handler"
import React from "react"
import { useTranslation } from "react-i18next"
import { useDispatch, useSelector } from "react-redux"
import { useAccount } from "wagmi"

function AppContent() {
  useConversationConfig()
  const { t } = useTranslation()
  const { data: settings } = useSettings()
  const { conversationId } = useConversation()
  const account = useAccount()
  const { data: conversation, isFetched } = useUserConversation(
    conversationId || null,
  )

  const { initialPrompt, files } = useSelector(
    (state: RootState) => state.initialQuery,
  )
  const { currentPathViewed } = useSelector(
    (state: RootState) => state.fileState,
  )

  const dispatch = useDispatch()
  const endSession = useEndSession()

  const [width, setWidth] = React.useState(window.innerWidth)
  // Set the document title to the conversation title when available
  useDocumentTitleFromState()

  // const Terminal = React.useMemo(
  //   () => React.lazy(() => import("#/components/features/terminal/terminal")),
  //   [],
  // );

  React.useEffect(() => {
    if (isFetched && !conversation) {
      displayErrorToast(
        "This conversation does not exist, or you do not have permission to access it.",
      )
      endSession()
    }
  }, [conversation, isFetched])

  React.useEffect(() => {
    dispatch(clearMessages())
    dispatch(clearTerminal())
    dispatch(clearJupyter())
    dispatch(clearComputerList())
    if (conversationId && (initialPrompt || files.length > 0)) {
      dispatch(
        addUserMessage({
          content: initialPrompt || "",
          imageUrls: files || [],
          timestamp: new Date().toISOString(),
          pending: true,
        }),
      )
      dispatch(clearInitialPrompt())
      dispatch(clearFiles())
    }
  }, [conversationId])

  useEffectOnce(() => {
    dispatch(clearMessages())
    dispatch(clearTerminal())
    dispatch(clearJupyter())
  })

  function handleResize() {
    setWidth(window.innerWidth)
  }

  React.useEffect(() => {
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
    }
  }, [])

  function renderMain() {
    if (width <= 640) {
      return (
        <div className="w-full overflow-hidden rounded-xl border border-neutral-600">
          <ChatInterface />
        </div>
      )
    }
    return (
      <ResizablePanel
        orientation={Orientation.HORIZONTAL}
        className="h-full min-h-0 min-w-0 grow"
        initialSize={800}
        firstClassName="rounded-xl overflow-hidden "
        secondClassName="flex flex-col overflow-hidden"
        firstChild={<ChatInterface />}
        secondChild={
          <Container className="!mb-4 mt-4 h-full rounded-xl border-none bg-white">
            {currentPathViewed ? (
              <ViewFile currentPathViewed={currentPathViewed} />
            ) : (
              <ThesisComputer />
            )}
          </Container>
        }
      />
    )
  }

  {
    /* <Container
            className="h-full mt-4 rounded-xl !mb-4"
            labels={[
              {
                label: t(I18nKey.WORKSPACE$TITLE),
                to: "",
                icon: <CodeIcon />,
              },
              // { label: "Jupyter", to: "jupyter", icon: <ListIcon /> },
              // {
              //   label: <ServedAppLabel />,
              //   to: "served",
              //   icon: <FaServer />,
              // },
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
          </Container> */
  }

  return (
    <WsClientProvider conversationId={conversationId}>
      <FilesProvider>
        <EventHandler>
          <div data-testid="app-route" className="flex h-full flex-col gap-3">
            <div className="flex h-full overflow-auto">{renderMain()}</div>

            {/*
          <Controls
            setSecurityOpen={onSecurityModalOpen}
            showSecurityLock={!!settings?.SECURITY_ANALYZER}
          /> */}
            {/* {settings && (
            <Security
              isOpen={securityModalIsOpen}
              onOpenChange={onSecurityModalOpenChange}
              securityAnalyzer={settings.SECURITY_ANALYZER}
            />
          )} */}
          </div>
        </EventHandler>
      </FilesProvider>
    </WsClientProvider>
  )
}

function App() {
  return (
    <ConversationProvider>
      <AppContent />
    </ConversationProvider>
  )
}

export default App
