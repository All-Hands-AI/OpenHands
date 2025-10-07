import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import { useWebSocket } from "#/hooks/use-websocket";
import { useEventStore } from "#/stores/use-event-store";

interface ConversationWebSocketContextType {
  connectionState: "CONNECTING" | "OPEN" | "CLOSED" | "CLOSING";
}

const ConversationWebSocketContext = createContext<
  ConversationWebSocketContextType | undefined
>(undefined);

export function ConversationWebSocketProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [connectionState, setConnectionState] = useState<
    "CONNECTING" | "OPEN" | "CLOSED" | "CLOSING"
  >("CONNECTING");
  const { addEvent } = useEventStore();

  const handleMessage = useCallback(
    (messageEvent: MessageEvent) => {
      try {
        const event = JSON.parse(messageEvent.data);
        // Basic validation - ensure it has required BaseEvent properties
        if (
          event &&
          typeof event === "object" &&
          event.id &&
          event.timestamp &&
          event.source
        ) {
          addEvent(event);
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn("Failed to parse WebSocket message as JSON:", error);
      }
    },
    [addEvent],
  );

  const websocketOptions = useMemo(
    () => ({
      onOpen: () => setConnectionState("OPEN"),
      onClose: () => setConnectionState("CLOSED"),
      onError: () => setConnectionState("CLOSED"),
      onMessage: handleMessage,
    }),
    [handleMessage],
  );

  const { socket } = useWebSocket(
    "ws://localhost/events/socket",
    websocketOptions,
  );

  useEffect(() => {
    if (socket) {
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
  }, [socket]);

  const contextValue = useMemo(() => ({ connectionState }), [connectionState]);

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
