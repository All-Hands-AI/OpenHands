import React from "react"
import { io, Socket } from "socket.io-client"
import EventLogger from "#/utils/event-logger"
import { handleAssistantMessage } from "#/services/actions"
import { showChatError } from "#/utils/error-handler"
import { useRate } from "#/hooks/use-rate"
import { OpenHandsParsedEvent } from "#/types/core"
import { AssistantMessageAction, UserMessageAction } from "#/types/core/actions"
import { useGetJwt } from "#/zutand-stores/persist-config/selector"
import { useLocation } from "react-router"
import { useDispatch } from "react-redux"
import { clearMessages } from "#/state/chat-slice"
import { setCurrentPathViewed } from "#/state/file-state-slice"
import { clearComputerList } from "#/state/computer-slice"

export const isOpenHandsEvent = (
  event: unknown,
): event is OpenHandsParsedEvent =>
  typeof event === "object" &&
  event !== null &&
  "id" in event &&
  "source" in event &&
  "message" in event &&
  "timestamp" in event

export const isUserMessage = (
  event: OpenHandsParsedEvent,
): event is UserMessageAction =>
  "source" in event &&
  "type" in event &&
  event.source === "user" &&
  event.type === "message"

export const isAssistantMessage = (
  event: OpenHandsParsedEvent,
): event is AssistantMessageAction =>
  "source" in event &&
  "type" in event &&
  event.source === "agent" &&
  event.type === "message"

export const isMessageAction = (
  event: OpenHandsParsedEvent,
): event is UserMessageAction | AssistantMessageAction =>
  isUserMessage(event) || isAssistantMessage(event)

export enum WsClientProviderStatus {
  CONNECTED,
  DISCONNECTED,
}

export enum ReplayStatus {
  IN_PROGRESS,
  COMPLETED,
}

interface UseWsClient {
  status: WsClientProviderStatus
  isLoadingMessages: boolean
  events: Record<string, unknown>[]
  send: (event: Record<string, unknown>) => void
  disconnect: () => void
  skipToResults: () => void
  replayStatus: ReplayStatus
  resetReplay: () => void
}

const WsClientContext = React.createContext<UseWsClient>({
  status: WsClientProviderStatus.DISCONNECTED,
  isLoadingMessages: true,
  events: [],
  send: () => {
    throw new Error("not connected")
  },
  disconnect: () => {
    throw new Error("not connected")
  },
  skipToResults: () => {
    throw new Error("not connected")
  },
  replayStatus: ReplayStatus.IN_PROGRESS,
  resetReplay: () => {
    throw new Error("not connected")
  },
})

export interface WsClientProviderProps {
  conversationId: string
}

export interface ErrorArg {
  message?: string
  data?: ErrorArgData | unknown
}

export interface ErrorArgData {
  msg_id: string
}

export function updateStatusWhenErrorMessagePresent(data: ErrorArg | unknown) {
  const isObject = (val: unknown): val is object =>
    !!val && typeof val === "object"
  const isString = (val: unknown): val is string => typeof val === "string"
  if (isObject(data) && "message" in data && isString(data.message)) {
    if (data.message === "websocket error" || data.message === "timeout") {
      return
    }
    let msgId: string | undefined
    let metadata: Record<string, unknown> = {}

    if ("data" in data && isObject(data.data)) {
      if ("msg_id" in data.data && isString(data.data.msg_id)) {
        msgId = data.data.msg_id
      }
      metadata = data.data as Record<string, unknown>
    }

    showChatError({
      message: data.message,
      source: "websocket",
      metadata,
      msgId,
    })
  }
}

export function WsClientProvider({
  conversationId,
  children,
}: React.PropsWithChildren<WsClientProviderProps>) {
  const sioRef = React.useRef<Socket | null>(null)
  const [status, setStatus] = React.useState(
    WsClientProviderStatus.DISCONNECTED,
  )
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([])
  const [replayStatus, setReplayStatus] = React.useState<ReplayStatus>(
    ReplayStatus.IN_PROGRESS,
  )
  const lastEventRef = React.useRef<Record<string, unknown> | null>(null)
  const messageQueueRef = React.useRef<Record<string, unknown>[]>([])
  const processingQueueRef = React.useRef<boolean>(false)
  const jwt = useGetJwt()
  const location = useLocation()
  const dispatch = useDispatch()

  const messageRateHandler = useRate({ threshold: 250 })

  const isShareRoute = React.useMemo(() => {
    return location.pathname.startsWith("/share/")
  }, [location.pathname])

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.error("WebSocket is not connected.")
      return
    }
    sioRef.current.emit("oh_user_action", event)
  }

  function disconnect() {
    const sio = sioRef.current
    if (sio) {
      sio.off("connect", handleConnect)
      sio.off("oh_event", handleMessage)
      sio.off("connect_error", handleError)
      sio.off("connect_failed", handleError)
      sio.off("disconnect", handleDisconnect)
      sio.disconnect()
      sioRef.current = null // Clear the ref after disconnecting
      setStatus(WsClientProviderStatus.DISCONNECTED)
    }
  }

  function handleConnect() {
    setStatus(WsClientProviderStatus.CONNECTED)
  }

  function resetReplay() {
    setReplayStatus(ReplayStatus.IN_PROGRESS)

    const savedEvents = [...events]
    setEvents([])

    messageQueueRef.current = savedEvents

    processingQueueRef.current = false

    dispatch(clearMessages())
    dispatch(setCurrentPathViewed(""))
    dispatch(clearComputerList())

    processMessageQueue()
  }

  function skipToResults() {
    if (messageQueueRef.current.length === 0) {
      return
    }

    processingQueueRef.current = true
    const allEvents = [...messageQueueRef.current]
    messageQueueRef.current = []

    setEvents((prevEvents) => [...prevEvents, ...allEvents])

    if (allEvents.length > 0) {
      const lastEvent = allEvents[allEvents.length - 1]
      if (!Number.isNaN(parseInt(lastEvent.id as string, 10))) {
        lastEventRef.current = lastEvent
      }
    }

    allEvents.forEach((event) => {
      handleAssistantMessage(event)
    })

    setReplayStatus(ReplayStatus.COMPLETED)
    processingQueueRef.current = false
  }

  function processMessageQueue() {
    if (processingQueueRef.current || messageQueueRef.current.length === 0) {
      if (messageQueueRef.current.length === 0 && !processingQueueRef.current) {
        setReplayStatus(ReplayStatus.COMPLETED)
      }
      return
    }

    processingQueueRef.current = true
    const event = messageQueueRef.current.shift()

    if (event) {
      setEvents((prevEvents) => [...prevEvents, event])
      if (!Number.isNaN(parseInt(event.id as string, 10))) {
        lastEventRef.current = event
      }

      handleAssistantMessage(event)

      setTimeout(() => {
        processingQueueRef.current = false
        if (messageQueueRef.current.length === 0) {
          setReplayStatus(ReplayStatus.COMPLETED)
        }
        processMessageQueue()
      }, 1000)
    } else {
      processingQueueRef.current = false
      setReplayStatus(ReplayStatus.COMPLETED)
    }
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsEvent(event) && isMessageAction(event)) {
      messageRateHandler.record(new Date().getTime())
    }

    if (isShareRoute) {
      messageQueueRef.current.push(event)
      processMessageQueue()
    } else {
      setEvents((prevEvents) => [...prevEvents, event])
      if (!Number.isNaN(parseInt(event.id as string, 10))) {
        lastEventRef.current = event
      }
      handleAssistantMessage(event)
    }
  }

  function handleDisconnect(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED)
    const sio = sioRef.current
    if (!sio) {
      return
    }
    sio.io.opts.query = sio.io.opts.query || {}
    sio.io.opts.query.latest_event_id = lastEventRef.current?.id
    updateStatusWhenErrorMessagePresent(data)
  }

  function handleError(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED)
    updateStatusWhenErrorMessagePresent(data)
  }

  // Combined useEffect to handle both cleanup and reconnection
  React.useEffect(() => {
    if (!conversationId) {
      throw new Error("No conversation ID provided")
    }

    if (sioRef.current) {
      const sio = sioRef.current
      sio.off("connect", handleConnect)
      sio.off("oh_event", handleMessage)
      sio.off("connect_error", handleError)
      sio.off("connect_failed", handleError)
      sio.off("disconnect", handleDisconnect)
      sio.disconnect()
      sioRef.current = null
    }

    lastEventRef.current = null

    messageQueueRef.current = []
    processingQueueRef.current = false
    setReplayStatus(ReplayStatus.IN_PROGRESS)

    const query = {
      latest_event_id: -1,
      conversation_id: conversationId,
      auth: jwt,
    }

    const baseUrl =
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host

    const sio = io(baseUrl, {
      transports: ["websocket"],
      query,
    })
    sio.on("connect", handleConnect)
    sio.on("oh_event", handleMessage)
    sio.on("connect_error", handleError)
    sio.on("connect_failed", handleError)
    sio.on("disconnect", handleDisconnect)

    sioRef.current = sio

    // No cleanup function to run in background
  }, [conversationId, jwt])

  const value = React.useMemo<UseWsClient>(
    () => ({
      status,
      isLoadingMessages: messageRateHandler.isUnderThreshold,
      events,
      send,
      disconnect,
      skipToResults,
      replayStatus,
      resetReplay,
    }),
    [status, messageRateHandler.isUnderThreshold, events, replayStatus],
  )

  return (
    <WsClientContext.Provider value={value}>
      {children}
    </WsClientContext.Provider>
  )
}

export function useWsClient() {
  const context = React.useContext(WsClientContext)
  return context
}
