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
import { WsClientProvider } from "#/context/ws-client-provider"
import { useConversationConfig } from "#/hooks/query/use-conversation-config"
import { useSettings } from "#/hooks/query/use-settings"
import { useUserConversation } from "#/hooks/query/use-user-conversation"
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state"
import { useSelector } from "react-redux"
import { RootState } from "#/store"
import React from "react"
import { useTranslation } from "react-i18next"

function ShareContent() {
  useConversationConfig()
  const { t } = useTranslation()
  const { data: settings } = useSettings()
  const { conversationId } = useConversation()
  const { data: conversation, isFetched } = useUserConversation(
    conversationId || null,
  )

  const { currentPathViewed } = useSelector(
    (state: RootState) => state.fileState,
  )

  const [width, setWidth] = React.useState(window.innerWidth)
  // Set the document title to the conversation title when available
  useDocumentTitleFromState()

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
        initialSize={700}
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

  return (
    <WsClientProvider conversationId={conversationId}>
      <div className="flex h-full flex-col gap-3">
        <div className="flex h-full overflow-auto">{renderMain()}</div>
      </div>
    </WsClientProvider>
  )
}

function Share() {
  return (
    <ConversationProvider>
      <ShareContent />
    </ConversationProvider>
  )
}

export default Share
