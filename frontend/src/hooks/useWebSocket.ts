import React from "react";
import { clearToken, getToken, setToken } from "#/services/auth";

export const useWebSocket = (host: string) => {
  const [socket, setSocket] = React.useState<WebSocket | null>(null);

  /**
   * Initialize the WebSocket connection. Close the existing connection if it exists.
   */
  const initializeWebSocket = React.useCallback(() => {
    if (socket) {
      socket.close();
      clearToken();
      setSocket(null);
    }

    const url = new URL(`ws://${host}/ws`);

    const token = getToken();
    if (token) url.searchParams.set("token", token);

    const websocket = new WebSocket(url.toString());
    setSocket(websocket);

    websocket.onmessage = (event) => {
      // set token if it is received from the server
      const message = JSON.parse(event.data);
      if (message.status === "ok" && message.token) {
        setToken(message.token);
      }
    };
  }, [socket]);

  React.useEffect(() => {
    initializeWebSocket();

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  return { socket, initializeWebSocket };
};
