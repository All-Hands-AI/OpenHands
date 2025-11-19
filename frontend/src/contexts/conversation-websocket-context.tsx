import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
  useRef,
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
  isConversationErrorEvent,
} from "#/types/v1/type-guards";
import { handleActionEventCacheInvalidation } from "#/utils/cache-utils";
import { buildWebSocketUrl } from "#/utils/websocket-url";
import { isBudgetOrCreditError } from "#/utils/error-handler";
import type { V1SendMessageRequest } from "#/api/conversation-service/v1-conversation-service.types";
import EventService from "#/api/event-service/event-service.api";
import { useTracking } from "#/hooks/use-tracking";

// eslint-disable-next-line @typescript-eslint/naming-convention
export type V1_WebSocketConnectionState =
  | "CONNECTING"
  | "OPEN"
  | "CLOSED"
  | "CLOSING";

interface ConversationWebSocketContextType {
  connectionState: V1_WebSocketConnectionState;
  sendMessage: (message: V1SendMessageRequest) => Promise<void>;
  isLoadingHistory: boolean;
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
  const { setExecutionStatus } = useV1ConversationStateStore();
  const { appendInput, appendOutput } = useCommandStore();
  const { trackCreditLimitReached } = useTracking();

  // History loading state
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [expectedEventCount, setExpectedEventCount] = useState<number | null>(
    null,
  );
  const receivedEventCountRef = useRef(0);

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

  // Reset hasConnected flag and history loading state when conversation changes
  useEffect(() => {
    hasConnectedRef.current = false;
    setIsLoadingHistory(true);
    setExpectedEventCount(null);
    receivedEventCountRef.current = 0;
  }, [conversationId]);

  // Check if we've received all events when expectedEventCount becomes available
  useEffect(() => {
    if (
      expectedEventCount !== null &&
      receivedEventCountRef.current >= expectedEventCount &&
      isLoadingHistory
    ) {
      setIsLoadingHistory(false);
    }
  }, [expectedEventCount, isLoadingHistory]);

  const handleMessage = useCallback(
    (messageEvent: MessageEvent) => {
      try {
        const event = JSON.parse(messageEvent.data);

        // Track received events for history loading (count ALL events from WebSocket)
        // Always count when loading, even if we don't have the expected count yet
        if (isLoadingHistory) {
          receivedEventCountRef.current += 1;

          if (
            expectedEventCount !== null &&
            receivedEventCountRef.current >= expectedEventCount
          ) {
            setIsLoadingHistory(false);
          }
        }

        // Use type guard to validate v1 event structure
        if (isV1Event(event)) {
          addEvent(event);

          // Handle ConversationErrorEvent specifically
          if (isConversationErrorEvent(event)) {
            setErrorMessage(event.detail);
          }

          // Handle AgentErrorEvent specifically
          if (isAgentErrorEvent(event)) {
            setErrorMessage(event.error);

            // Track credit limit reached if the error is budget-related
            if (isBudgetOrCreditError(event.error)) {
              trackCreditLimitReached({
                conversationId: conversationId || "unknown",
              });
            }
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
              setExecutionStatus(event.value.execution_status);
            }
            if (isAgentStatusConversationStateUpdateEvent(event)) {
              setExecutionStatus(event.value);
            }
          }

          // Handle ExecuteBashAction events - add command as input to terminal
          if (isExecuteBashActionEvent(event)) {
            appendInput(event.action.command);
          }

          // Handle ExecuteBashObservation events - add output to terminal
          if (isExecuteBashObservationEvent(event)) {
            // Extract text content from the observation content array
            const textContent = event.observation.content
              .filter((c) => c.type === "text")
              .map((c) => c.text)
              .join("\n");
            appendOutput(textContent);
          }
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn("Failed to parse WebSocket message as JSON:", error);
      }
    },
    [
      addEvent,
      isLoadingHistory,
      expectedEventCount,
      setErrorMessage,
      removeOptimisticUserMessage,
      queryClient,
      conversationId,
      setExecutionStatus,
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
      onOpen: async () => {
        setConnectionState("OPEN");
        hasConnectedRef.current = true; // Mark that we've successfully connected
        removeErrorMessage(); // Clear any previous error messages on successful connection

        // Fetch expected event count for history loading detection
        if (conversationId) {
          try {
            const count = await EventService.getEventCount(conversationId);
            setExpectedEventCount(count);

            // If no events expected, mark as loaded immediately
            if (count === 0) {
              setIsLoadingHistory(false);
            }
          } catch (error) {
            // Fall back to marking as loaded to avoid infinite loading state
            setIsLoadingHistory(false);
          }
        }
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
  }, [
    handleMessage,
    setErrorMessage,
    removeErrorMessage,
    sessionApiKey,
    conversationId,
  ]);

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
    () => ({ connectionState, sendMessage, isLoadingHistory }),
    [connectionState, sendMessage, isLoadingHistory],
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
