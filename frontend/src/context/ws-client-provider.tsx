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
    EventLogger.info(`Queueing message: ${JSON.stringify(event)}`);
    setPendingMessages((prev) => [...prev, event]);
  }

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.error("WebSocket is not connected, queueing message");
      queueMessage(event);
      return;
    }

    // Always send the message to the backend, which will handle queueing if needed
    EventLogger.info(`Sending message to backend: ${JSON.stringify(event)}`);
    sioRef.current.emit("oh_action", event);
  }

  function handleConnect() {
    EventLogger.info("WebSocket connected");
    setStatus(WsClientProviderStatus.CONNECTED);

    // Set a timeout to consider the backend ready after a short delay
    // This is a fallback in case we don't receive any events from the backend
    setTimeout(() => {
      if (!backendReady) {
        EventLogger.info(
          "Backend ready timeout reached, forcing backend ready state",
        );
        setBackendReady(true);
      }
    }, 1000); // 1 second timeout

    EventLogger.info(
      `Connection established, waiting for backend ready signal. Pending messages: ${pendingMessages.length}`,
    );
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsEvent(event) && isMessageAction(event)) {
      messageRateHandler.record(new Date().getTime());
    }

    // Consider the backend ready as soon as we receive any event
    if (!backendReady) {
      EventLogger.info(
        `Received first event from backend, setting backend ready. Event: ${JSON.stringify(event)}`,
      );
      setBackendReady(true);
    }

    setEvents((prevEvents) => [...prevEvents, event]);
    if (!Number.isNaN(parseInt(event.id as string, 10))) {
      lastEventRef.current = event;
    }

    handleAssistantMessage(event);
  }

  function handleDisconnect(data: unknown) {
    EventLogger.info("WebSocket disconnected");
    setStatus(WsClientProviderStatus.DISCONNECTED);
    setBackendReady(false);
    const sio = sioRef.current;
    if (!sio) {
      return;
    }
    sio.io.opts.query = sio.io.opts.query || {};
    sio.io.opts.query.latest_event_id = lastEventRef.current?.id;
    EventLogger.info(
      `Disconnect with latest event ID: ${lastEventRef.current?.id}`,
    );
    updateStatusWhenErrorMessagePresent(data);
  }

  function handleError(data: unknown) {
    EventLogger.error(`WebSocket connection error: ${JSON.stringify(data)}`);
    setStatus(WsClientProviderStatus.DISCONNECTED);
    setBackendReady(false);
    updateStatusWhenErrorMessagePresent(data);
  }

  // Process any pending messages when the WebSocket connects
  React.useEffect(() => {
    EventLogger.info(
      `Connection status: ${status}, Pending messages: ${pendingMessages.length}`,
    );

    if (
      status === WsClientProviderStatus.CONNECTED &&
      pendingMessages.length > 0 &&
      sioRef.current
    ) {
      // We're connected and have pending messages
      EventLogger.info(
        `Connected! Sending ${pendingMessages.length} queued messages`,
      );

      pendingMessages.forEach((event, index) => {
        EventLogger.info(
          `Sending queued message ${index + 1}/${pendingMessages.length}: ${JSON.stringify(event)}`,
        );
        sioRef.current?.emit("oh_action", event);
      });

      setPendingMessages([]);
      EventLogger.info("All queued messages sent, queue cleared");
    }
  }, [status, pendingMessages.length]);

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
