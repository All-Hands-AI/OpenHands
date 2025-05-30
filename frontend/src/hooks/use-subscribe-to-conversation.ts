import { useCallback } from "react";
import toast from "react-hot-toast";
import { useSocketIO } from "./use-socket-io";
import {
  isAgentStateChangeObservation,
  isOpenHandsEvent,
} from "#/types/core/guards";

export interface UseSubscribeToConversationOptions {
  conversation_id: string;
  providers_set: ("github" | "gitlab")[];
  // Have to set the session_api_key here because socketio doesn't support
  // custom headers when only enabling the WebSocket transport
  session_api_key: string | null;
}

export const useSubscribeToConversation = () => {
  const handleOhEvent = useCallback((event: unknown) => {
    console.warn(event);
    if (isOpenHandsEvent(event)) {
      if (isAgentStateChangeObservation(event)) {
        toast(event.extras.agent_state, {
          id: "status",
          duration: Infinity,
          position: "top-right",
        });
      }
    }
  }, []);

  // Create event handlers object with the callback
  const eventHandlers = {
    oh_event: handleOhEvent,
  };

  // Use the socket hook with the event handlers
  const { connect, isConnected, isConnecting, error, socket } =
    useSocketIO(eventHandlers);

  return {
    connect,
    isConnected,
    isConnecting,
    error,
    socket,
  };
};
