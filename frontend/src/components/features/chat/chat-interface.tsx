import { useWsClient } from "#/context/ws-client-provider"
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom"
import { generateAgentStateChangeEvent } from "#/services/agent-state-service"
import { createChatMessage } from "#/services/chat-service"
import { addUserMessage } from "#/state/chat-slice"
import { RootState } from "#/store"
import { AgentState } from "#/types/agent-state"
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64"
import posthog from "posthog-js"
import React, { useEffect } from "react"
import { useDispatch, useSelector } from "react-redux"
import { useParams } from "react-router"
import { FeedbackModal } from "../feedback/feedback-modal"
import { TrajectoryActions } from "../trajectory/trajectory-actions"
import { ActionSuggestions } from "./action-suggestions"
import { ChatSuggestions } from "./chat-suggestions"
import { InteractiveChatBox } from "./interactive-chat-box"
import { Messages } from "./messages"
import { TypingIndicator } from "./typing-indicator"
import { FaPowerOff } from "react-icons/fa6"
import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button"
import { LoadingSpinner } from "#/components/shared/loading-spinner"
import Security from "#/components/shared/modals/security/security"
import { WsClientProviderStatus } from "#/context/ws-client-provider"
import { useGetTrajectory } from "#/hooks/mutation/use-get-trajectory"
import { useListFiles } from "#/hooks/query/use-list-files"
import { useSettings } from "#/hooks/query/use-settings"
import { I18nKey } from "#/i18n/declaration"
import { setCurrentPathViewed } from "#/state/file-state-slice"
import { displayErrorToast } from "#/utils/custom-toast-handlers"
import { downloadTrajectory } from "#/utils/download-trajectory"
import { useDisclosure } from "@heroui/react"
import { useTranslation } from "react-i18next"
import { FaFileInvoice } from "react-icons/fa"
import { Controls } from "../controls/controls"

function getEntryPoint(
  hasRepository: boolean | null,
  hasReplayJson: boolean | null,
): string {
  if (hasRepository) return "github"
  if (hasReplayJson) return "replay"
  return "direct"
}

export function ChatInterface() {
  const { data: settings } = useSettings()
  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure()
  const dispatch = useDispatch()
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const { send, isLoadingMessages, disconnect, status } = useWsClient()
  const { t } = useTranslation()
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef)

  const { messages } = useSelector((state: RootState) => state.chat)
  const { curAgentState } = useSelector((state: RootState) => state.agent)
  const { data: files, refetch: refetchFiles } = useListFiles({
    isCached: false,
    enabled: true,
  })

  useEffect(() => {
    if (curAgentState === AgentState.AWAITING_USER_INPUT) refetchFiles()
  }, [curAgentState])

  // Scroll to bottom when files are loaded
  useEffect(() => {
    if (files && files.length > 0) {
      scrollDomToBottom()
    }
  }, [files])

  const [feedbackPolarity, setFeedbackPolarity] = React.useState<
    "positive" | "negative"
  >("positive")
  const [feedbackModalIsOpen, setFeedbackModalIsOpen] = React.useState(false)
  const [messageToSend, setMessageToSend] = React.useState<string | null>(null)
  const { selectedRepository, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  )
  const params = useParams()
  const { mutate: getTrajectory } = useGetTrajectory()

  const handleSendMessage = async (content: string, files: File[]) => {
    if (messages.length === 0) {
      posthog.capture("initial_query_submitted", {
        entry_point: getEntryPoint(
          selectedRepository !== null,
          replayJson !== null,
        ),
        query_character_length: content.length,
        replay_json_size: replayJson?.length,
      })
    } else {
      posthog.capture("user_message_sent", {
        session_message_count: messages.length,
        current_message_length: content.length,
      })
    }
    const promises = files.map((file) => convertImageToBase64(file))
    const imageUrls = await Promise.all(promises)

    const timestamp = new Date().toISOString()
    const pending = true
    dispatch(addUserMessage({ content, imageUrls, timestamp, pending }))
    send(createChatMessage(content, imageUrls, timestamp))
    setMessageToSend(null)
  }

  const handleStop = () => {
    posthog.capture("stop_button_clicked")
    send(generateAgentStateChangeEvent(AgentState.STOPPED))
  }

  const handleDisconnect = () => {
    posthog.capture("websocket_disconnect_clicked")
    disconnect()
  }

  const onClickShareFeedbackActionButton = async (
    polarity: "positive" | "negative",
  ) => {
    setFeedbackModalIsOpen(true)
    setFeedbackPolarity(polarity)
  }

  const onClickExportTrajectoryButton = () => {
    if (!params.conversationId) {
      displayErrorToast(t(I18nKey.CONVERSATION$DOWNLOAD_ERROR))
      return
    }

    getTrajectory(params.conversationId, {
      onSuccess: async (data) => {
        await downloadTrajectory(
          params.conversationId ?? t(I18nKey.CONVERSATION$UNKNOWN),
          data.trajectory,
        )
      },
      onError: () => {
        displayErrorToast(t(I18nKey.CONVERSATION$DOWNLOAD_ERROR))
      },
    })
  }

  const isWaitingForUserInput =
    curAgentState === AgentState.AWAITING_USER_INPUT ||
    curAgentState === AgentState.FINISHED

  return (
    <div className="mx-auto flex h-full max-w-[800px] flex-col justify-between">
      {messages.length === 0 && (
        <ChatSuggestions onSuggestionsClick={setMessageToSend} />
      )}

      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="fast-smooth-scroll flex grow flex-col gap-2 overflow-y-auto overflow-x-hidden px-4 pt-4"
      >
        {isLoadingMessages && (
          <div className="flex justify-center">
            <LoadingSpinner size="small" />
          </div>
        )}

        {!isLoadingMessages && (
          <Messages
            messages={messages}
            isAwaitingUserConfirmation={
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION
            }
          />
        )}

        {isWaitingForUserInput && (
          <ActionSuggestions
            onSuggestionsClick={(value) => handleSendMessage(value, [])}
          />
        )}

        {files && files.length > 0 && (
          <div className="my-3 flex flex-wrap gap-2">
            {files.map((file) => (
              <div
                key={file}
                className="flex w-fit max-w-full cursor-pointer items-center gap-2 rounded-md bg-neutral-1000 p-2 hover:opacity-70"
                onClick={() => dispatch(setCurrentPathViewed(file))}
              >
                <FaFileInvoice className="h-4 w-4 shrink-0 fill-blue-500" />
                <div className="line-clamp-1 text-sm">{file}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-[6px] px-4 pb-4">
        <div className="relative flex justify-between">
          <TrajectoryActions
            onPositiveFeedback={() =>
              onClickShareFeedbackActionButton("positive")
            }
            onNegativeFeedback={() =>
              onClickShareFeedbackActionButton("negative")
            }
            onExportTrajectory={() => onClickExportTrajectoryButton()}
          />

          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 transform">
            {curAgentState === AgentState.RUNNING && <TypingIndicator />}
          </div>

          {!hitBottom && <ScrollToBottomButton onClick={scrollDomToBottom} />}
        </div>

        <div className="flex items-center gap-2">
          <InteractiveChatBox
            onSubmit={handleSendMessage}
            onStop={handleStop}
            isDisabled={
              curAgentState === AgentState.LOADING ||
              curAgentState === AgentState.AWAITING_USER_CONFIRMATION ||
              status === WsClientProviderStatus.DISCONNECTED
            }
            mode={curAgentState === AgentState.RUNNING ? "stop" : "submit"}
            value={messageToSend ?? undefined}
            onChange={setMessageToSend}
            className="w-full flex-grow" // Ensure chat box takes full width minus space for the button
          />
        </div>
        <div className="flex w-full items-center justify-between gap-2">
          {/* {settings && (
            <Security
              isOpen={securityModalIsOpen}
              onOpenChange={onSecurityModalOpenChange}
              securityAnalyzer={settings.SECURITY_ANALYZER}
            />
          )} */}
          <Controls
            setSecurityOpen={onSecurityModalOpen}
            showSecurityLock={!!settings?.SECURITY_ANALYZER}
          />
          <DisconnectButton
            handleDisconnect={handleDisconnect}
            isDisabled={
              !isWaitingForUserInput &&
              status !== WsClientProviderStatus.DISCONNECTED
            }
          />
        </div>
      </div>

      <FeedbackModal
        isOpen={feedbackModalIsOpen}
        onClose={() => setFeedbackModalIsOpen(false)}
        polarity={feedbackPolarity}
      />
    </div>
  )
}

interface DisconnectButtonProps {
  handleDisconnect: () => void
  isDisabled: boolean
}

export function DisconnectButton({
  handleDisconnect,
  isDisabled,
}: DisconnectButtonProps) {
  const { t } = useTranslation()

  if (isDisabled) {
    return null
  }

  return (
    <button
      title="Disconnect"
      onClick={handleDisconnect}
      disabled={isDisabled}
      className={`rounded-lg px-3 py-2 font-medium transition-colors ${
        isDisabled
          ? "cursor-not-allowed bg-red-200"
          : "bg-red-100 text-red-500 hover:bg-red-50"
      }`}
    >
      <FaPowerOff />
      {/* {t(isDisabled ? "Connect" : "Disconnect")} */}
    </button>
  )
}
