import React from "react";
import { getToken } from "#/services/auth";
import { handleAssistantMessage } from "#/services/actions";
import { generateAgentInitEvent, generateUserMessageEvent } from "./utils";

const HOST = "localhost:3000";

interface SessionContextType {
  sendUserMessage: (message: string, images_urls: string[]) => void;
  eventLog: string[];
}

const SessionContext = React.createContext<SessionContextType | undefined>(
  undefined,
);

function SessionProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = React.useState<WebSocket | null>(null);
  const [eventLog, setEventLog] = React.useState<string[]>([]);

  const pushToEventLog = (message: string) => {
    console.log(message);
    setEventLog((prev) => [...prev, message]);
  };

  React.useEffect(() => {
    const url = new URL(`ws://${HOST}/ws`);

    const token = getToken();
    if (token) url.searchParams.set("token", token);

    const websocket = new WebSocket(url.toString());
    setSocket(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  React.useEffect(() => {
    if (socket) {
      socket.onopen = () => {
        // initialize agent
        const event = generateAgentInitEvent();
        socket.send(event);
      };

      socket.onmessage = (event) => {
        pushToEventLog(event.data);
        // TODO: better handle the messages; e.g. use eventLog directly in the UI
        handleAssistantMessage(JSON.parse(event.data));
      };

      socket.onerror = () => {
        // TODO: handle error
      };

      socket.onclose = () => {
        // TODO: reconnect
      };
    }
  }, [socket]);

  const sendMessageToSocket = (message: string) => {
    if (socket) {
      pushToEventLog(message);
      socket.send(message);
    }
  };

  /**
   * Send a message to the assistant
   * @param message The message to send
   * @param images_urls Array of image urls
   */
  const sendUserMessage = (message: string, images_urls: string[]) => {
    const event = generateUserMessageEvent(message, images_urls);
    sendMessageToSocket(event);
  };

  // TODO: sendTerminalCommand
  // TODO: sendAgentStateChange

  const value = React.useMemo(
    () => ({ sendUserMessage, eventLog }),
    [sendUserMessage, eventLog],
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
