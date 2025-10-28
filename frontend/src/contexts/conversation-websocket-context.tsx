import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket, WebSocketHookOptions } from "#/hooks/use-websocket";
import { useEventStore } from "#/stores/use-event-store";
import { useErrorMessageStore } from "#/stores/error-message-store";
import { useOptimisticUserMessageStore } from "#/stores/optimistic-user-message-store";
import { useV1ConversationStateStore } from "#/stores/v1-conversation-state-store";
import { useCommandStore } from "#/state/command-store";
import {
  isV1Event,
  isAgentErrorEvent,
  isUserMessageEvent,
  isActionEvent,
  isConversationStateUpdateEvent,
  isFullStateConversationStateUpdateEvent,
  isAgentStatusConversationStateUpdateEvent,
  isExecuteBashActionEvent,
  isExecuteBashObservationEvent,
} from "#/types/v1/type-guards";
import { handleActionEventCacheInvalidation } from "#/utils/cache-utils";
import { buildWebSocketUrl } from "#/utils/websocket-url";
import type { V1SendMessageRequest } from "#/api/conversation-service/v1-conversation-service.types";

// eslint-disable-next-line @typescript-eslint/naming-convention
export type V1_WebSocketConnectionState =
  | "CONNECTING"
  | "OPEN"
  | "CLOSED"
  | "CLOSING";

interface ConversationWebSocketContextType {
  connectionState: V1_WebSocketConnectionState;
  sendMessage: (message: V1SendMessageRequest) => Promise<void>;
}

const ConversationWebSocketContext = createContext<
  ConversationWebSocketContextType | undefined
>(undefined);

export function ConversationWebSocketProvider({
  children,
  conversationId,
  conversationUrl,
  sessionApiKey,
}: {
  children: React.ReactNode;
  conversationId?: string;
  conversationUrl?: string | null;
  sessionApiKey?: string | null;
}) {
  const [connectionState, setConnectionState] =
    useState<V1_WebSocketConnectionState>("CONNECTING");
  // Track if we've ever successfully connected
  // Don't show errors until after first successful connection
  const hasConnectedRef = React.useRef(false);
  const queryClient = useQueryClient();
  const { addEvent } = useEventStore();
  const { setErrorMessage, removeErrorMessage } = useErrorMessageStore();
  const { removeOptimisticUserMessage } = useOptimisticUserMessageStore();
  const { setAgentStatus } = useV1ConversationStateStore();
  const { appendInput, appendOutput } = useCommandStore();

  // Build WebSocket URL from props
  // Only build URL if we have both conversationId and conversationUrl
  // This prevents connection attempts during task polling phase
  const wsUrl = useMemo(() => {
    // Don't attempt connection if we're missing required data
    if (!conversationId || !conversationUrl) {
      return null;
    }
    return buildWebSocketUrl(conversationId, conversationUrl);
  }, [conversationId, conversationUrl]);

  // Reset hasConnected flag when conversation changes
  useEffect(() => {
    hasConnectedRef.current = false;
  }, [conversationId]);

  const handleMessage = useCallback(
    (messageEvent: MessageEvent) => {
      try {
        const event = JSON.parse(messageEvent.data);

        // Use type guard to validate v1 event structure
        if (isV1Event(event)) {
          addEvent(event);

          // Handle AgentErrorEvent specifically
          if (isAgentErrorEvent(event)) {
            setErrorMessage(event.error);
          }

          // Clear optimistic user message when a user message is confirmed
          if (isUserMessageEvent(event)) {
            removeOptimisticUserMessage();
          }

          // Handle cache invalidation for ActionEvent
          if (isActionEvent(event)) {
            const currentConversationId =
              conversationId || "test-conversation-id"; // TODO: Get from context
            handleActionEventCacheInvalidation(
              event,
              currentConversationId,
              queryClient,
            );
          }

          // Handle conversation state updates
          // TODO: Tests
          if (isConversationStateUpdateEvent(event)) {
            if (isFullStateConversationStateUpdateEvent(event)) {
              setAgentStatus(event.value.agent_status);
            }
            if (isAgentStatusConversationStateUpdateEvent(event)) {
              setAgentStatus(event.value);
            }
          }

          // Handle ExecuteBashAction events - add command as input to terminal
          if (isExecuteBashActionEvent(event)) {
            appendInput(event.action.command);
          }

          // Handle ExecuteBashObservation events - add output to terminal
          if (isExecuteBashObservationEvent(event)) {
            appendOutput(event.observation.output);
          }
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn("Failed to parse WebSocket message as JSON:", error);
      }
    },
    [
      addEvent,
      setErrorMessage,
      removeOptimisticUserMessage,
      queryClient,
      conversationId,
      setAgentStatus,
      appendInput,
      appendOutput,
    ],
  );

  const websocketOptions: WebSocketHookOptions = useMemo(() => {
    const queryParams: Record<string, string | boolean> = {
      resend_all: true,
    };

    // Add session_api_key if available
    if (sessionApiKey) {
      queryParams.session_api_key = sessionApiKey;
    }

    return {
      queryParams,
      reconnect: { enabled: true },
      onOpen: () => {
        setConnectionState("OPEN");
        hasConnectedRef.current = true; // Mark that we've successfully connected
        removeErrorMessage(); // Clear any previous error messages on successful connection
      },
      onClose: (event: CloseEvent) => {
        setConnectionState("CLOSED");
        // Only show error message if we've previously connected successfully
        // This prevents showing errors during initial connection attempts (e.g., when auto-starting a conversation)
        if (event.code !== 1000 && hasConnectedRef.current) {
          setErrorMessage(
            `Connection lost: ${event.reason || "Unexpected disconnect"}`,
          );
        }
      },
      onError: () => {
        setConnectionState("CLOSED");
        // Only show error message if we've previously connected successfully
        if (hasConnectedRef.current) {
          setErrorMessage("Failed to connect to server");
        }
      },
      onMessage: handleMessage,
    };
  }, [handleMessage, setErrorMessage, removeErrorMessage, sessionApiKey]);

  // Only attempt WebSocket connection when we have a valid URL
  // This prevents connection attempts during task polling phase
  const websocketUrl = wsUrl;
  const { socket } = useWebSocket(websocketUrl || "", websocketOptions);

  // V1 send message function via WebSocket
  const sendMessage = useCallback(
    async (message: V1SendMessageRequest) => {
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        const error = "WebSocket is not connected";
        setErrorMessage(error);
        throw new Error(error);
      }

      try {
        // Send message through WebSocket as JSON
        socket.send(JSON.stringify(message));
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to send message";
        setErrorMessage(errorMessage);
        throw error;
      }
    },
    [socket, setErrorMessage],
  );

  useEffect(() => {
    // Only process socket updates if we have a valid URL and socket
    if (socket && wsUrl) {
      // Update state based on socket readyState
      const updateState = () => {
        switch (socket.readyState) {
          case WebSocket.CONNECTING:
            setConnectionState("CONNECTING");
            break;
          case WebSocket.OPEN:
            setConnectionState("OPEN");
            break;
          case WebSocket.CLOSING:
            setConnectionState("CLOSING");
            break;
          case WebSocket.CLOSED:
            setConnectionState("CLOSED");
            break;
          default:
            setConnectionState("CLOSED");
            break;
        }
      };

      updateState();
    }
  }, [socket, wsUrl]);

  const contextValue = useMemo(
    () => ({ connectionState, sendMessage }),
    [connectionState, sendMessage],
  );

  return (
    <ConversationWebSocketContext.Provider value={contextValue}>
      {children}
    </ConversationWebSocketContext.Provider>
  );
}

export const useConversationWebSocket =
  (): ConversationWebSocketContextType | null => {
    const context = useContext(ConversationWebSocketContext);
    // Return null instead of throwing when not in provider
    // This allows the hook to be called conditionally based on conversation version
    return context || null;
  };
