import React, { useCallback } from "react";
import toast from "react-hot-toast";
import { useSocketIO } from "./use-socket-io";

import { useConversationId } from "./use-conversation-id";

export interface UseSubscribeToConversationOptions {
  conversation_id: string;
  providers_set: ("github" | "gitlab")[];
  // Have to set the session_api_key here because socketio doesn't support
  // custom headers when only enabling the WebSocket transport
  session_api_key: string | null;
}

export const useSubscribeToConversation = () => {
  const { conversationId: currentConversationId } = useConversationId();

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

  React.useEffect(() => {
    disconnect();
    toast.dismiss("status");
  }, [currentConversationId]);

  return {
    connect: handleConnect,
    isConnected,
    isConnecting,
    error,
    socket,
  };
};
