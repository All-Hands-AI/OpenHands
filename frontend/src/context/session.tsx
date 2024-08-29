import React from "react";
import { getToken } from "#/services/auth";
import { handleAssistantMessage } from "#/services/actions";
import {
  generateAgentInitEvent,
  generateAgentStateChangeEvent,
  generateUserMessageEvent,
  generateUserTerminalCommandEvent,
} from "./utils";

const isAgentStateChangeEvent = (event: object): event is AgentStateChange =>
  "observation" in event && event.observation === "agent_state_changed";

const HOST = "localhost:3000";

interface SessionContextType {
  sendUserMessage: (message: string, images_urls: string[]) => void;
  sendTerminalCommand: (command: string) => void;
  triggerAgentStateChange: (agent_state: AgentState) => void;
  agentState: AgentState;
  eventLog: string[];
}

const SessionContext = React.createContext<SessionContextType | undefined>(
  undefined,
);

function SessionProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = React.useState<WebSocket | null>(null);
  const [agentState, setAgentState] = React.useState<AgentState>("loading");
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
        const message = JSON.parse(event.data);

        if (isAgentStateChangeEvent(message)) {
          setAgentState(message.extras.agent_state);
        }
        // TODO: better handle the messages; e.g. use eventLog directly in the UI
        handleAssistantMessage(message);
      };

      socket.onerror = () => {
        console.error("Socket error");
        // TODO: handle error
      };

      socket.onclose = () => {
        console.error("Socket closed");
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

  /**
   * Send a terminal command inputted by the user to the assistant
   * @param command The command input by the user
   */
  const sendTerminalCommand = (command: string) => {
    // FIXME: `socket` is not defined when this function is called
    const event = generateUserTerminalCommandEvent(command);
    sendMessageToSocket(event);
  };

  /**
   * Send a change in agent state to the assistant
   * @param agent_state The new agent state
   */
  const triggerAgentStateChange = (agent_state: AgentState) => {
    const event = generateAgentStateChangeEvent(agent_state);
    sendMessageToSocket(event);
  };

  const value = React.useMemo(
    () => ({
      sendUserMessage,
      sendTerminalCommand,
      triggerAgentStateChange,
      agentState,
      eventLog,
    }),
    [
      sendUserMessage,
      sendTerminalCommand,
      triggerAgentStateChange,
      agentState,
      eventLog,
    ],
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
