import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "#/hooks/use-websocket";
import { useEventStore } from "#/stores/use-event-store";
import { useErrorMessageStore } from "#/stores/error-message-store";
import { useOptimisticUserMessageStore } from "#/stores/optimistic-user-message-store";
import { useV1ConversationStateStore } from "#/stores/v1-conversation-state-store";
import {
  isV1Event,
  isAgentErrorEvent,
  isUserMessageEvent,
  isActionEvent,
  isConversationStateUpdateEvent,
} from "#/types/v1/type-guards";
import { handleActionEventCacheInvalidation } from "#/utils/cache-utils";
import { buildWebSocketUrl } from "#/utils/websocket-url";
import V1ConversationService, {
  V1SendMessageRequest,
} from "#/api/conversation-service/v1-conversation-service.api";

interface ConversationWebSocketContextType {
  connectionState: "CONNECTING" | "OPEN" | "CLOSED" | "CLOSING";
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
  const [connectionState, setConnectionState] = useState<
    "CONNECTING" | "OPEN" | "CLOSED" | "CLOSING"
  >("CONNECTING");
  const queryClient = useQueryClient();
  const { addEvent } = useEventStore();
  const { setErrorMessage, removeErrorMessage } = useErrorMessageStore();
  const { removeOptimisticUserMessage } = useOptimisticUserMessageStore();
  const { setAgentStatus } = useV1ConversationStateStore();

  // V1 send message function via HTTP POST API
  const sendMessage = useCallback(
    async (message: V1SendMessageRequest) => {
      if (!conversationId) {
        throw new Error("No conversation ID provided");
      }

      try {
        await V1ConversationService.sendMessage(conversationId, message);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to send message";
        setErrorMessage(errorMessage);
        throw error;
      }
    },
    [conversationId, setErrorMessage],
  );

  // Build WebSocket URL from props
  const wsUrl = useMemo(
    () => buildWebSocketUrl(conversationId, conversationUrl, sessionApiKey),
    [conversationId, conversationUrl, sessionApiKey],
  );

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
            setAgentStatus(event.value.agent_status);
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
    ],
  );

  const websocketOptions = useMemo(
    () => ({
      onOpen: () => {
        setConnectionState("OPEN");
        removeErrorMessage(); // Clear any previous error messages on successful connection
      },
      onClose: (event: CloseEvent) => {
        setConnectionState("CLOSED");
        // Set error message for unexpected disconnects (not normal closure)
        if (event.code !== 1000) {
          setErrorMessage(
            `Connection lost: ${event.reason || "Unexpected disconnect"}`,
          );
        }
      },
      onError: () => {
        setConnectionState("CLOSED");
        setErrorMessage("Failed to connect to server");
      },
      onMessage: handleMessage,
    }),
    [handleMessage, setErrorMessage, removeErrorMessage],
  );

  // Build a fallback URL to prevent hook from connecting if conversation data isn't ready
  const websocketUrl = wsUrl || "ws://localhost/placeholder";
  const { socket } = useWebSocket(websocketUrl, websocketOptions);

  useEffect(() => {
    // Only process socket updates if we have a valid URL
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
  (): ConversationWebSocketContextType => {
    const context = useContext(ConversationWebSocketContext);
    if (context === undefined) {
      throw new Error(
        "useConversationWebSocket must be used within a ConversationWebSocketProvider",
      );
    }
    return context;
  };
