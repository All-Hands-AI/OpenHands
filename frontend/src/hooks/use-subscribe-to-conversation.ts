import React, { useCallback } from "react";
import { useSocketIO } from "./use-socket-io";

export interface UseSubscribeToConversationOptions {
  conversation_id: string;
  providers_set: ("github" | "gitlab")[];
  // Have to set the session_api_key here because socketio doesn't support
  // custom headers when only enabling the WebSocket transport
  session_api_key: string | null;
}

export const useSubscribeToConversation = () => {
  // Create a callback for the oh_event handler
  const handleOhEvent = useCallback((data: any) => {
    console.log("Received oh_event in useSubscribeToConversation:", data);
    // Here you would typically dispatch this data to your state management
    // or call other functions to handle the event
  }, []);

  // Create event handlers object with the callback
  const eventHandlers = {
    oh_event: handleOhEvent,
  };

  // Use the socket hook with the event handlers
  const { connect, isConnected, isConnecting, error, socket } = useSocketIO(eventHandlers);

  // Log connection status changes
  React.useEffect(() => {
    if (isConnected) {
      console.log("Socket connection established in useSubscribeToConversation");
    }
  }, [isConnected]);

  // Log when socket changes
  React.useEffect(() => {
    if (socket) {
      console.log("Socket reference updated in useSubscribeToConversation", socket);
      
      // Verify event listeners
      const listeners = socket.listeners("oh_event");
      console.log(`Number of oh_event listeners: ${listeners.length}`);
    }
  }, [socket]);

  return {
    connect,
    isConnected,
    isConnecting,
    error,
    socket,
  };
};
