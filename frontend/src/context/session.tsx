import React from "react";
import { getToken } from "#/services/auth";
import { handleAssistantMessage } from "#/services/actions";
import {
  generateAgentInitEvent,
  generateAgentStateChangeEvent,
  generateUserMessageEvent,
  generateUserTerminalCommandEvent,
} from "./utils";
import { extractMessage, ParsedMessage } from "#/utils/extractMessage";
import {
  extractTerminalStream,
  TerminalStream,
} from "#/utils/extractTerminalStream";
import { extractJupyterCell, JupyterCell } from "#/utils/extractJupyterCells";

const isAgentStateChangeEvent = (event: object): event is AgentStateChange =>
  "observation" in event && event.observation === "agent_state_changed";

const isBrowseObservation = (message: object): message is BrowseObservation =>
  "observation" in message && message.observation === "browse";

export const isAddTaskAction = (message: object): message is AddTaskAction =>
  "action" in message && message.action === "add_task";

interface ParsedData {
  // aggregated data
  messages: ParsedMessage[];
  terminalStreams: TerminalStream[];
  jupyterCells: JupyterCell[];
  // individual data
  browseState: BrowseObservation | null;
  taskState: AddTaskAction | null;
  agentState: AgentState;
}

const HOST = "localhost:3000";

interface SessionContextType {
  sendUserMessage: (message: string, images_urls: string[]) => void;
  sendTerminalCommand: (command: string) => void;
  triggerAgentStateChange: (agent_state: AgentState) => void;
  eventLog: string[];
  data: ParsedData;
}

const SessionContext = React.createContext<SessionContextType | undefined>(
  undefined,
);

function SessionProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = React.useState<WebSocket | null>(null);
  const [eventLog, setEventLog] = React.useState<string[]>([]);

  // parsed data that is used throughout the app
  const [data, setData] = React.useState<ParsedData>({
    messages: [],
    terminalStreams: [],
    jupyterCells: [],
    browseState: null,
    taskState: null,
    agentState: "loading",
  });

  const pushToEventLog = (message: string) => {
    console.log(message);
    setEventLog((prev) => [...prev, message]);
  };

  const sendMessageToSocket = (message: string) => {
    if (socket) {
      pushToEventLog(message);
      socket.send(message);
    }
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
        const message = JSON.parse(event.data) as TrajectoryItem;

        const parsedMessage = extractMessage(message);
        if (parsedMessage) {
          setData((prev) => ({
            ...prev,
            messages: [...prev.messages, parsedMessage],
          }));
        }

        const terminalStream = extractTerminalStream(message);
        if (terminalStream) {
          setData((prev) => ({
            ...prev,
            terminalStreams: [...prev.terminalStreams, terminalStream],
          }));
        }

        const jupyterCell = extractJupyterCell(message);
        if (jupyterCell) {
          setData((prev) => ({
            ...prev,
            jupyterCells: [...prev.jupyterCells, jupyterCell],
          }));
        }

        if (isBrowseObservation(message)) {
          setData((prev) => ({
            ...prev,
            browseState: message,
          }));
        }

        if (isAddTaskAction(message)) {
          setData((prev) => ({
            ...prev,
            taskState: message,
          }));
        }

        if (isAgentStateChangeEvent(message)) {
          setData((prev) => ({
            ...prev,
            agentState: message.args.agent_state,
          }));
        }

        // TODO: remove after full replacement
        handleAssistantMessage(message);
      };

      socket.onerror = () => {
        console.warn("Socket error");
        // TODO: handle error
      };

      socket.onclose = () => {
        console.warn("Socket closed");
        // TODO: reconnect
      };
    }
  }, [socket]);

  /**
   * Append a user message to the message log. This is used when the user sends a message from the client.
   * @param message The message to append
   * @param images_urls Array of image urls
   */
  const appendUserMessage = (message: string, images_urls: string[]) => {
    const parsed: ParsedMessage = {
      source: "user",
      content: message,
      imageUrls: images_urls,
    };
    setData((prev) => ({
      ...prev,
      messages: [...prev.messages, parsed],
    }));
  };

  /**
   * Send a message to the assistant
   * @param message The message to send
   * @param images_urls Array of image urls
   */
  const sendUserMessage = (message: string, images_urls: string[]) => {
    const event = generateUserMessageEvent(message, images_urls);
    sendMessageToSocket(event);
    appendUserMessage(message, images_urls); // add the message to the message log since the socket doesn't return the message
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
      eventLog,
      data,
    }),
    [
      sendUserMessage,
      sendTerminalCommand,
      triggerAgentStateChange,
      eventLog,
      data,
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
