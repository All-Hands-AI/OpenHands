import { useWsClient } from "#/context/ws-client-provider"
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom"
import { generateAgentStateChangeEvent } from "#/services/agent-state-service"
import { createChatMessage } from "#/services/chat-service"
import { addUserMessage } from "#/state/chat-slice"
import { RootState } from "#/store"
import { AgentState } from "#/types/agent-state"
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64"
import posthog from "posthog-js"
import React from "react"
import { useDispatch, useSelector } from "react-redux"
import { useParams } from "react-router"
import { FeedbackModal } from "../feedback/feedback-modal"
import { TrajectoryActions } from "../trajectory/trajectory-actions"
import { ActionSuggestions } from "./action-suggestions"
import { ChatSuggestions } from "./chat-suggestions"
import { InteractiveChatBox } from "./interactive-chat-box"
import { Messages } from "./messages"
import { TypingIndicator } from "./typing-indicator"

import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button"
import { LoadingSpinner } from "#/components/shared/loading-spinner"
import Security from "#/components/shared/modals/security/security"
import { useGetTrajectory } from "#/hooks/mutation/use-get-trajectory"
import { useSettings } from "#/hooks/query/use-settings"
import { displayErrorToast } from "#/utils/custom-toast-handlers"
import { downloadTrajectory } from "#/utils/download-trajectory"
import { useDisclosure } from "@heroui/react"
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
  const { send, isLoadingMessages } = useWsClient()
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } =
    useScrollToBottom(scrollRef)

  const { messages } = useSelector((state: RootState) => state.chat)
  const { curAgentState } = useSelector((state: RootState) => state.agent)

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

  const onClickShareFeedbackActionButton = async (
    polarity: "positive" | "negative",
  ) => {
    setFeedbackModalIsOpen(true)
    setFeedbackPolarity(polarity)
  }

  const onClickExportTrajectoryButton = () => {
    if (!params.conversationId) {
      displayErrorToast("ConversationId unknown, cannot download trajectory")
      return
    }

    getTrajectory(params.conversationId, {
      onSuccess: async (data) => {
        await downloadTrajectory(
          params.conversationId ?? "unknown",
          data.trajectory,
        )
      },
      onError: (error) => {
        displayErrorToast(error.message)
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
        className="flex grow flex-col gap-2 overflow-y-auto overflow-x-hidden px-4 pt-4"
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

        <InteractiveChatBox
          onSubmit={handleSendMessage}
          onStop={handleStop}
          isDisabled={
            curAgentState === AgentState.LOADING ||
            curAgentState === AgentState.AWAITING_USER_CONFIRMATION
          }
          mode={curAgentState === AgentState.RUNNING ? "stop" : "submit"}
          value={messageToSend ?? undefined}
          onChange={setMessageToSend}
        />
        <Controls
          setSecurityOpen={onSecurityModalOpen}
          showSecurityLock={!!settings?.SECURITY_ANALYZER}
        />
        {settings && (
          <Security
            isOpen={securityModalIsOpen}
            onOpenChange={onSecurityModalOpenChange}
            securityAnalyzer={settings.SECURITY_ANALYZER}
          />
        )}
      </div>

      <FeedbackModal
        isOpen={feedbackModalIsOpen}
        onClose={() => setFeedbackModalIsOpen(false)}
        polarity={feedbackPolarity}
      />
    </div>
  )
}
