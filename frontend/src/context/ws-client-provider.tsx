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
  const lastEventRef = React.useRef<Record<string, unknown> | null>(null);

  const messageRateHandler = useRate({ threshold: 250 });

  // Private function to queue messages for later sending
  const queueMessage = (event: Record<string, unknown>) => {
    EventLogger.info(`Queueing message: ${JSON.stringify(event)}`);
    setPendingMessages((prev) => [...prev, event]);
  };

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.info("WebSocket is not connected, queueing message");
      queueMessage(event);
      return;
    }

    // Send the message to the backend
    EventLogger.info(`Sending message: ${JSON.stringify(event)}`);
    sioRef.current.emit("oh_action", event);
  }

  function handleConnect() {
    setStatus(WsClientProviderStatus.CONNECTED);
    EventLogger.info(
      `WebSocket connected. Pending messages: ${pendingMessages.length}`,
    );
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsEvent(event) && isMessageAction(event)) {
      messageRateHandler.record(new Date().getTime());
    }

    setEvents((prevEvents) => [...prevEvents, event]);
    if (!Number.isNaN(parseInt(event.id as string, 10))) {
      lastEventRef.current = event;
    }

    handleAssistantMessage(event);
  }

  function handleDisconnect(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED);
    const sio = sioRef.current;
    if (!sio) {
      return;
    }
    sio.io.opts.query = sio.io.opts.query || {};
    sio.io.opts.query.latest_event_id = lastEventRef.current?.id;
    EventLogger.info(
      `WebSocket disconnected. Latest event ID: ${lastEventRef.current?.id}`,
    );
    updateStatusWhenErrorMessagePresent(data);
  }

  function handleError(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED);
    EventLogger.error(`WebSocket connection error: ${JSON.stringify(data)}`);
    updateStatusWhenErrorMessagePresent(data);
  }

  // Process any pending messages when the WebSocket connects
  React.useEffect(() => {
    if (
      status === WsClientProviderStatus.CONNECTED &&
      pendingMessages.length > 0 &&
      sioRef.current
    ) {
      // We're connected and have pending messages
      EventLogger.info(
        `Connected! Sending ${pendingMessages.length} queued messages`,
      );

      pendingMessages.forEach((event) => {
        sioRef.current?.emit("oh_action", event);
      });

      setPendingMessages([]);
      EventLogger.info("All queued messages sent, queue cleared");
    }
  }, [status, pendingMessages.length]);

  React.useEffect(() => {
    lastEventRef.current = null;
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
    }),
    [status, messageRateHandler.isUnderThreshold, events, pendingMessages],
  );

  return <WsClientContext value={value}>{children}</WsClientContext>;
}

export function useWsClient() {
  const context = React.useContext(WsClientContext);
  return context;
}
