import React from "react";
import { io, Socket } from "socket.io-client";
import { useQueryClient } from "@tanstack/react-query";
import EventLogger from "#/utils/event-logger";
import { handleAssistantMessage } from "#/services/actions";
import { showChatError } from "#/utils/error-handler";
import { useRate } from "#/hooks/use-rate";
import { OpenHandsParsedEvent } from "#/types/core";
import {
  AssistantMessageAction,
  CommandAction,
  FileEditAction,
  FileWriteAction,
  UserMessageAction,
} from "#/types/core/actions";
import { Conversation } from "#/api/open-hands.types";
import { useUserProviders } from "#/hooks/use-user-providers";

const isOpenHandsEvent = (event: unknown): event is OpenHandsParsedEvent =>
  typeof event === "object" &&
  event !== null &&
  "id" in event &&
  "source" in event &&
  "message" in event &&
  "timestamp" in event;

const isFileWriteAction = (
  event: OpenHandsParsedEvent,
): event is FileWriteAction => "action" in event && event.action === "write";

const isFileEditAction = (
  event: OpenHandsParsedEvent,
): event is FileEditAction => "action" in event && event.action === "edit";

const isCommandAction = (event: OpenHandsParsedEvent): event is CommandAction =>
  "action" in event && event.action === "run";

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
}

const WsClientContext = React.createContext<UseWsClient>({
  status: WsClientProviderStatus.DISCONNECTED,
  isLoadingMessages: true,
  events: [],
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
    if (data.message === "websocket error" || data.message === "timeout") {
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
  const queryClient = useQueryClient();
  const sioRef = React.useRef<Socket | null>(null);
  const reconnectAttempts = React.useRef(0);
  const reconnectTimeout = React.useRef<NodeJS.Timeout>();
  const [status, setStatus] = React.useState(
    WsClientProviderStatus.DISCONNECTED,
  );
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);
  const lastEventRef = React.useRef<Record<string, unknown> | null>(null);
  const { providers } = useUserProviders();

  const messageRateHandler = useRate({ threshold: 250 });

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.error("WebSocket is not connected.");
      return;
    }
    sioRef.current.emit("oh_user_action", event);
  }

  /**
   * @author vbs_0
   * Handles successful WebSocket connection and resets reconnection state
   */
  function handleConnect() {
    setStatus(WsClientProviderStatus.CONNECTED);
    reconnectAttempts.current = 0;
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsEvent(event)) {
      if (isMessageAction(event)) {
        messageRateHandler.record(new Date().getTime());
      }

      // Invalidate diffs cache when a file is edited or written
      if (
        isFileEditAction(event) ||
        isFileWriteAction(event) ||
        isCommandAction(event)
      ) {
        queryClient.invalidateQueries({
          queryKey: ["file_changes", conversationId],
        });

        // Invalidate file diff cache when a file is edited or written
        if (!isCommandAction(event)) {
          const cachedConversaton = queryClient.getQueryData<Conversation>([
            "user",
            "conversation",
            conversationId,
          ]);
          const clonedRepositoryDirectory =
            cachedConversaton?.selected_repository?.split("/").pop();

          let fileToInvalidate = event.args.path.replace("/workspace/", "");
          if (clonedRepositoryDirectory) {
            fileToInvalidate = fileToInvalidate.replace(
              `${clonedRepositoryDirectory}/`,
              "",
            );
          }

          queryClient.invalidateQueries({
            queryKey: ["file_diff", conversationId, fileToInvalidate],
          });
        }
      }
    }

    setEvents((prevEvents) => [...prevEvents, event]);
    if (!Number.isNaN(parseInt(event.id as string, 10))) {
      lastEventRef.current = event;
    }

    handleAssistantMessage(event);
  }

  /**
   * @author vbs_0
   * Handles WebSocket disconnection with exponential backoff retry
   * Ensures only one socket is managed at a time and prevents duplicate connections
   */
  const handleDisconnect = React.useCallback(() => {
    setStatus(WsClientProviderStatus.DISCONNECTED);

    if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
      console.error("Max reconnection attempts reached");
      return;
    }

    if (sioRef.current) {
      sioRef.current.close();
      sioRef.current = null;
    }

    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }

    const backoffDelay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current) * (0.5 + Math.random()),
      MAX_RECONNECT_DELAY
    );

    reconnectTimeout.current = setTimeout(() => {
      reconnectAttempts.current++;
      console.log(
        `Attempting to reconnect (${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})`
      );
      connectToWs();
    }, backoffDelay);
  }, [connectToWs]);

  function handleError(data: unknown) {
    setStatus(WsClientProviderStatus.DISCONNECTED);
    updateStatusWhenErrorMessagePresent(data);
  }

  /**
   * @author vbs_0
   * Establishes WebSocket connection with improved error handling and state management
   * Uses the same URL logic as the rest of the file for consistency
   */
  const connectToWs = React.useCallback(() => {
    if (sioRef.current) {
      sioRef.current.close();
      sioRef.current = null;
    }

    setStatus(WsClientProviderStatus.CONNECTING);

    const lastEvent = lastEventRef.current;
    const query = {
      latest_event_id: lastEvent?.id ?? -1,
      conversation_id: conversationId,
      providers_set: providers,
    };
    const baseUrl = import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;

    try {
      const socket = io(baseUrl, {
        transports: ["websocket"],
        query,
      });

      socket.on("connect", handleConnect);
      socket.on("oh_event", handleMessage);
      socket.on("connect_error", handleError);
      socket.on("connect_failed", handleError);
      socket.on("disconnect", handleDisconnect);

      sioRef.current = socket;
    } catch (error) {
      console.error("Failed to establish WebSocket connection:", error);
      handleDisconnect();
    }
  }, [conversationId, providers, handleConnect, handleDisconnect, handleError, handleMessage]);

  /**
   * @author vbs_0
   * Effect to manage WebSocket connection lifecycle and cleanup
   * Only one socket is created and managed at a time
   */
  React.useEffect(() => {
    connectToWs();
    return () => {
      if (sioRef.current) {
        sioRef.current.close();
        sioRef.current = null;
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      reconnectAttempts.current = 0;
    };
  }, [connectToWs]);

  React.useEffect(() => {
    lastEventRef.current = null;
  }, [conversationId]);

  // (Removed duplicate disconnect cleanup effect)

  const value = React.useMemo<UseWsClient>(
    () => ({
      status,
      isLoadingMessages: messageRateHandler.isUnderThreshold,
      events,
      send,
    }),
    [status, messageRateHandler.isUnderThreshold, events],
  );

  return <WsClientContext value={value}>{children}</WsClientContext>;
}

export function useWsClient() {
  const context = React.useContext(WsClientContext);
  return context;
}

/**
 * WebSocket reconnection constants and state management
 * @author vbs_0
 * Implements exponential backoff for reconnection attempts to fix terminal update issues
 */
const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;
