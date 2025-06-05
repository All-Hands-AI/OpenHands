import { useCallback } from "react";
import { useSocketIO } from "./use-socket-io";

export interface UseSubscribeToConversationOptions {
  conversation_id: string;
  providers_set: ("github" | "gitlab")[];
  // Have to set the session_api_key here because socketio doesn't support
  // custom headers when only enabling the WebSocket transport
  session_api_key: string | null;
}

export const useSubscribeToConversation = () => {
  // Use the socket hook with the event handlers
  const { connect, disconnect, isConnected, isConnecting, error, socket } =
    useSocketIO();

  const handleConnect = useCallback(
    (
      url: string,
      options: UseSubscribeToConversationOptions,
      eventHandlers?: Record<string, (data: unknown) => void>,
    ) =>
      connect(
        {
          url,
          query: options,
        },
        eventHandlers,
      ),
    [connect],
  );

  const handleReconnect = useCallback(
    (
      url: string,
      options: UseSubscribeToConversationOptions,
      eventHandlers?: Record<string, (data: unknown) => void>,
    ) => {
      disconnect();
      connect(
        {
          url,
          query: options,
        },
        eventHandlers,
      );
    },
    [connect, disconnect],
  );

  return {
    connect: handleConnect,
    reconnect: handleReconnect,
    disconnect,
    isConnected,
    isConnecting,
    error,
    socket,
  };
};
