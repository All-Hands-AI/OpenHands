import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
} from "react";
import { io, Socket } from "socket.io-client";
import { createChatMessage } from "#/services/chat-service";
import { OpenHandsParsedEvent } from "#/types/core";
import {
  isOpenHandsEvent,
  isAgentStateChangeObservation,
} from "#/types/core/guards";
import { AgentState } from "#/types/agent-state";
import {
  renderConversationErroredToast,
  renderConversationCreatedToast,
  renderConversationFinishedToast,
} from "#/components/features/chat/microagent/microagent-status-toast";

interface ConversationSocket {
  socket: Socket;
  isConnected: boolean;
  events: OpenHandsParsedEvent[];
}

interface ConversationSubscriptionsContextType {
  activeConversationIds: string[];
  subscribeToConversation: (options: {
    conversationId: string;
    sessionApiKey: string | null;
    providersSet: ("github" | "gitlab")[];
    baseUrl: string;
    onEvent?: (event: unknown, conversationId: string) => void;
  }) => void;
  unsubscribeFromConversation: (conversationId: string) => void;
  isSubscribedToConversation: (conversationId: string) => boolean;
  getEventsForConversation: (conversationId: string) => OpenHandsParsedEvent[];
}

const ConversationSubscriptionsContext =
  createContext<ConversationSubscriptionsContextType>({
    activeConversationIds: [],
    subscribeToConversation: () => {
      throw new Error("ConversationSubscriptionsProvider not initialized");
    },
    unsubscribeFromConversation: () => {
      throw new Error("ConversationSubscriptionsProvider not initialized");
    },
    isSubscribedToConversation: () => false,
    getEventsForConversation: () => [],
  });

const isErrorEvent = (
  event: unknown,
): event is { error: true; message: string } =>
  typeof event === "object" &&
  event !== null &&
  "error" in event &&
  event.error === true &&
  "message" in event &&
  typeof event.message === "string";

const isAgentStatusError = (event: unknown): event is OpenHandsParsedEvent =>
  isOpenHandsEvent(event) &&
  isAgentStateChangeObservation(event) &&
  event.extras.agent_state === AgentState.ERROR;

export function ConversationSubscriptionsProvider({
  children,
}: React.PropsWithChildren) {
  const [activeConversationIds, setActiveConversationIds] = useState<string[]>(
    [],
  );
  const [conversationSockets, setConversationSockets] = useState<
    Record<string, ConversationSocket>
  >({});
  const eventHandlersRef = useRef<Record<string, (event: unknown) => void>>({});

  // Cleanup function to remove all subscriptions when component unmounts
  useEffect(
    () => () => {
      console.warn("EFFECT DISCONNECT");
      Object.values(conversationSockets).forEach((socketData) => {
        if (socketData.socket) {
          socketData.socket.disconnect();
        }
      });
    },
    [conversationSockets],
  );

  const subscribeToConversation = useCallback(
    (options: {
      conversationId: string;
      sessionApiKey: string | null;
      providersSet: ("github" | "gitlab")[];
      baseUrl: string;
      onEvent?: (event: unknown, conversationId: string) => void;
    }) => {
      const { conversationId, sessionApiKey, providersSet, baseUrl, onEvent } =
        options;

      // If already subscribed, don't create a new subscription
      if (conversationSockets[conversationId]) {
        return;
      }

      // Create event handler for this subscription
      const handleOhEvent = (event: unknown) => {
        console.warn(`Event for conversation ${conversationId}:`, event);

        // Call the custom event handler if provided
        if (onEvent) {
          onEvent(event, conversationId);
        }

        // Update the events for this subscription
        if (isOpenHandsEvent(event)) {
          setConversationSockets((prev) => ({
            ...prev,
            [conversationId]: {
              ...prev[conversationId],
              events: [...(prev[conversationId]?.events || []), event],
            },
          }));
        }

        // Handle error events
        if (isErrorEvent(event) || isAgentStatusError(event)) {
          renderConversationErroredToast(
            isErrorEvent(event) ? event.message : "Unknown error",
            () => {
              // Reconnect logic
              if (conversationSockets[conversationId]?.socket) {
                conversationSockets[conversationId].socket.emit(
                  "oh_user_action",
                  createChatMessage("continue", [], new Date().toISOString()),
                );
                renderConversationCreatedToast(conversationId);
              }
            },
          );
        } else if (
          isOpenHandsEvent(event) &&
          isAgentStateChangeObservation(event)
        ) {
          if (event.extras.agent_state === AgentState.FINISHED) {
            renderConversationFinishedToast(conversationId);
          }
        }
      };

      // Store the event handler
      eventHandlersRef.current[conversationId] = handleOhEvent;

      // Create socket connection
      const socket = io(baseUrl, {
        transports: ["websocket"],
        query: {
          conversation_id: conversationId,
          session_api_key: sessionApiKey,
          providers_set: providersSet,
        },
      });

      // Set up event listeners
      socket.on("connect", () => {
        console.warn(`Socket for conversation ${conversationId} CONNECTED!`);
        setConversationSockets((prev) => ({
          ...prev,
          [conversationId]: {
            ...prev[conversationId],
            isConnected: true,
          },
        }));
      });

      socket.on("disconnect", () => {
        console.warn(`Socket for conversation ${conversationId} DISCONNECTED!`);
        setConversationSockets((prev) => ({
          ...prev,
          [conversationId]: {
            ...prev[conversationId],
            isConnected: false,
          },
        }));
      });

      socket.on("oh_event", handleOhEvent);

      // Add the socket to our state
      setConversationSockets((prev) => ({
        ...prev,
        [conversationId]: {
          socket,
          isConnected: socket.connected,
          events: [],
        },
      }));

      // Add to active conversation IDs
      setActiveConversationIds((prev) =>
        prev.includes(conversationId) ? prev : [...prev, conversationId],
      );
    },
    [conversationSockets],
  );

  const unsubscribeFromConversation = useCallback(
    (conversationId: string) => {
      console.warn(`Unsubscribing from conversation ${conversationId}`);
      if (conversationSockets[conversationId]) {
        // Remove event listeners
        const { socket } = conversationSockets[conversationId];
        const handler = eventHandlersRef.current[conversationId];

        if (socket && handler) {
          socket.off("oh_event", handler);
          socket.disconnect();
        }

        // Remove from state
        setConversationSockets((prev) => {
          const newSockets = { ...prev };
          delete newSockets[conversationId];
          return newSockets;
        });

        // Remove from active IDs
        setActiveConversationIds((prev) =>
          prev.filter((id) => id !== conversationId),
        );

        // Clean up event handler reference
        delete eventHandlersRef.current[conversationId];
      }
    },
    [conversationSockets],
  );

  const isSubscribedToConversation = useCallback(
    (conversationId: string) => !!conversationSockets[conversationId],
    [conversationSockets],
  );

  const getEventsForConversation = useCallback(
    (conversationId: string) =>
      conversationSockets[conversationId]?.events || [],
    [conversationSockets],
  );

  const value = React.useMemo(
    () => ({
      activeConversationIds,
      subscribeToConversation,
      unsubscribeFromConversation,
      isSubscribedToConversation,
      getEventsForConversation,
    }),
    [
      activeConversationIds,
      subscribeToConversation,
      unsubscribeFromConversation,
      isSubscribedToConversation,
      getEventsForConversation,
    ],
  );

  return (
    <ConversationSubscriptionsContext.Provider value={value}>
      {children}
    </ConversationSubscriptionsContext.Provider>
  );
}

export function useConversationSubscriptions() {
  return useContext(ConversationSubscriptionsContext);
}
