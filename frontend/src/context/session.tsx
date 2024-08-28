import React from "react";
import { getToken } from "#/services/auth";
import { handleAssistantMessage } from "#/services/actions";
import { generateAgentInitEvent } from "./utils";

const HOST = "localhost:3000";

interface SessionContextType {
  sendMessageToSocket: (message: string) => void;
  eventLog: string[];
}

const SessionContext = React.createContext<SessionContextType | undefined>(
  undefined,
);

function SessionProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = React.useState<WebSocket | null>(null);
  const [eventLog, setEventLog] = React.useState<string[]>([]);

  React.useEffect(() => {
    const url = new URL(`ws://${HOST}/ws`);

    const token = getToken();
    if (token) url.searchParams.set("token", token);

    const websocket = new WebSocket(url.toString());
    setSocket(websocket);

    websocket.onopen = () => {
      // initialize agent
      const event = generateAgentInitEvent();
      websocket.send(event);
    };

    websocket.onmessage = (event) => {
      setEventLog((prev) => [...prev, event.data]);
      // TODO: better handle the messages
      handleAssistantMessage(JSON.parse(event.data));
    };

    websocket.onerror = () => {
      // TODO: handle error
    };

    websocket.onclose = () => {
      // TODO: reconnect
    };

    return () => {
      websocket.close();
    };
  }, []);

  const sendMessageToSocket = React.useCallback((message: string) => {
    if (socket) socket.send(message);
  }, []);

  const value = React.useMemo(
    () => ({ sendMessageToSocket, eventLog }),
    [sendMessageToSocket, eventLog],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

const useSession = () => {
  const context = React.useContext(SessionContext);
  if (context === undefined) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
};

export { SessionProvider, useSession };
