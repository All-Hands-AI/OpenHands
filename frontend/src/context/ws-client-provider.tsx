import React from "react";
import { io, Socket } from "socket.io-client";
import EventLogger from "#/utils/event-logger";
import { handleAssistantMessage } from "#/services/actions";
import { showChatError } from "#/utils/error-handler";
import { useRate } from "#/hooks/use-rate";
import { OpenHandsParsedEvent } from "#/types/core";
import {
  AssistantMessageAction,
  UserMessageAction,
} from "#/types/core/actions";

const isOpenHandsEvent = (event: unknown): event is OpenHandsParsedEvent =>
  typeof event === "object" &&
  event !== null &&
  "id" in event &&
  "source" in event &&
  "message" in event &&
  "timestamp" in event;

const isUserMessage = (
  event: OpenHandsParsedEvent,
): event is UserMessageAction =>
  "source" in event &&
  "type" in event &&
  event.source === "user" &&
  event.type === "message";

const isAssistantMessage = (
  event: OpenHandsParsedEvent,
): event is AssistantMessageAction =>
  "source" in event &&
  "type" in event &&
  event.source === "agent" &&
  event.type === "message";

const isMessageAction = (
  event: OpenHandsParsedEvent,
): event is UserMessageAction | AssistantMessageAction =>
  isUserMessage(event) || isAssistantMessage(event);

// Check if an event is an agent state changed observation
const isAgentStateEvent = (event: Record<string, unknown>): boolean => 
  isOpenHandsEvent(event) && 
  "type" in event && 
  event.type === "observation" && 
  "observation_id" in event && 
  event.observation_id === "agent_state_changed";

export enum WsClientProviderStatus {
  CONNECTED,
  DISCONNECTED,
}

interface UseWsClient {
  status: WsClientProviderStatus;
  isLoadingMessages: boolean;
  events: Record<string, unknown>[];
  send: (event: Record<string, unknown>) => void;
  queueMessage: (event: Record<string, unknown>) => void;
  pendingMessages: Record<string, unknown>[];
}

const WsClientContext = React.createContext<UseWsClient>({
  status: WsClientProviderStatus.DISCONNECTED,
  isLoadingMessages: true,
  events: [],
  pendingMessages: [],
  send: () => {
    throw new Error("not connected");
  },
  queueMessage: () => {
    throw new Error("not connected");
  },
});

interface WsClientProviderProps {
  conversationId: string;
}

interface ErrorArg {
  message?: string;
  data?: ErrorArgData | unknown;
}

interface ErrorArgData {
  msg_id: string;
}

export function updateStatusWhenErrorMessagePresent(data: ErrorArg | unknown) {
  const isObject = (val: unknown): val is object =>
    !!val && typeof val === "object";
  const isString = (val: unknown): val is string => typeof val === "string";
  if (isObject(data) && "message" in data && isString(data.message)) {
    if (data.message === "websocket error") {
      return;
    }
    let msgId: string | undefined;
    let metadata: Record<string, unknown> = {};

    if ("data" in data && isObject(data.data)) {
      if ("msg_id" in data.data && isString(data.data.msg_id)) {
        msgId = data.data.msg_id;
      }
      metadata = data.data as Record<string, unknown>;
    }

    showChatError({
      message: data.message,
      source: "websocket",
      metadata,
      msgId,
    });
  }
}

export function WsClientProvider({
  conversationId,
  children,
}: React.PropsWithChildren<WsClientProviderProps>) {
  const sioRef = React.useRef<Socket | null>(null);
  const [status, setStatus] = React.useState(
    WsClientProviderStatus.DISCONNECTED,
  );
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);
  const [pendingMessages, setPendingMessages] = React.useState<
    Record<string, unknown>[]
  >([]);
  const [backendReady, setBackendReady] = React.useState(false);
  const lastEventRef = React.useRef<Record<string, unknown> | null>(null);

  const messageRateHandler = useRate({ threshold: 250 });

  function queueMessage(event: Record<string, unknown>) {
    setPendingMessages((prev) => [...prev, event]);
  }

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.error("WebSocket is not connected.");
      queueMessage(event);
      return;
    }
    
    if (!backendReady) {
      // If backend is not ready yet, queue the message
      EventLogger.info("Backend not ready, queueing message");
      queueMessage(event);
      return;
    }
    
    sioRef.current.emit("oh_action", event);
  }

  function handleConnect() {
    setStatus(WsClientProviderStatus.CONNECTED);
    // Don't send queued messages yet - wait for backend ready signal
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsEvent(event) && isMessageAction(event)) {
      messageRateHandler.record(new Date().getTime());
    }
    
    // Check if this is a state change event indicating backend is ready
    if (isAgentStateEvent(event)) {
      setBackendReady(true);
    }
    
    setEvents((prevEvents) => [...prevEvents, event]);
    if (!Number.isNaN(parseInt(event.id as string, 10))) {
      lastEventRef.current = event;
    }

    handleAssistantMessage(event);
  }

  function handleDisconnect(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED);
    setBackendReady(false);
    const sio = sioRef.current;
    if (!sio) {
      return;
    }
    sio.io.opts.query = sio.io.opts.query || {};
    sio.io.opts.query.latest_event_id = lastEventRef.current?.id;
    updateStatusWhenErrorMessagePresent(data);
  }

  function handleError(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED);
    setBackendReady(false);
    updateStatusWhenErrorMessagePresent(data);
  }

  // Watch for backend ready state and send queued messages when ready
  React.useEffect(() => {
    if (backendReady && pendingMessages.length > 0 && sioRef.current) {
      // Backend is ready and we have pending messages
      EventLogger.info(`Sending ${pendingMessages.length} queued messages`);
      
      pendingMessages.forEach((event) => {
        sioRef.current?.emit("oh_action", event);
      });

      // Also set the agent state to RUNNING if needed
      const agentStateEvent = {
        action: "change_agent_state",
        args: { agent_state: "running" },
      };
      sioRef.current.emit("oh_action", agentStateEvent);

      setPendingMessages([]);
    }
  }, [backendReady, pendingMessages.length]);

  React.useEffect(() => {
    lastEventRef.current = null;
    setBackendReady(false);
  }, [conversationId]);

  React.useEffect(() => {
    if (!conversationId) {
      throw new Error("No conversation ID provided");
    }

    let sio = sioRef.current;

    const lastEvent = lastEventRef.current;
    const query = {
      latest_event_id: lastEvent?.id ?? -1,
      conversation_id: conversationId,
    };

    const baseUrl =
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;

    sio = io(baseUrl, {
      transports: ["websocket"],
      query,
    });
    sio.on("connect", handleConnect);
    sio.on("oh_event", handleMessage);
    sio.on("connect_error", handleError);
    sio.on("connect_failed", handleError);
    sio.on("disconnect", handleDisconnect);

    sioRef.current = sio;

    return () => {
      sio.off("connect", handleConnect);
      sio.off("oh_event", handleMessage);
      sio.off("connect_error", handleError);
      sio.off("connect_failed", handleError);
      sio.off("disconnect", handleDisconnect);
    };
  }, [conversationId]);

  React.useEffect(
    () => () => {
      const sio = sioRef.current;
      if (sio) {
        sio.off("disconnect", handleDisconnect);
        sio.disconnect();
      }
    },
    [],
  );

  const value = React.useMemo<UseWsClient>(
    () => ({
      status,
      isLoadingMessages: messageRateHandler.isUnderThreshold,
      events,
      pendingMessages,
      send,
      queueMessage,
    }),
    [status, messageRateHandler.isUnderThreshold, events, pendingMessages],
  );

  return <WsClientContext value={value}>{children}</WsClientContext>;
}

export function useWsClient() {
  const context = React.useContext(WsClientContext);
  return context;
}
