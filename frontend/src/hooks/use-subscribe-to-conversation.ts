import { useSocketIO } from "./use-socket-io";

export interface UseSubscribeToConversationOptions {
  conversation_id: string;
  providers_set: ("github" | "gitlab")[];
  // Have to set the session_api_key here because socketio doesn't support
  // custom headers when only enabling the WebSocket transport
  session_api_key: string | null;
}

export const useSubscribeToConversation = () => {
  const { connect, isConnected, isConnecting, error } = useSocketIO({
    oh_event: (data: string) => {
      console.log(JSON.parse(data));
    },
  });

  return {
    connect,
    isConnected,
    isConnecting,
    error,
  };
};
