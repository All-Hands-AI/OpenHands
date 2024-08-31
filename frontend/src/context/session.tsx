import React from "react";
import { handleAssistantMessage } from "#/services/actions";
import {
  generateAgentInitEvent,
  generateAgentStateChangeEvent,
  generateUserMessageEvent,
  generateUserTerminalCommandEvent,
  isAddTaskAction,
  isAgentStateChangeEvent,
  isBrowseObservation,
} from "./utils";
import { extractMessage, ParsedMessage } from "#/utils/extractMessage";
import {
  extractTerminalStream,
  TerminalStream,
} from "#/utils/extractTerminalStream";
import { extractJupyterCell, JupyterCell } from "#/utils/extractJupyterCells";
import { useWebSocket } from "#/hooks/useWebSocket";
import { OpenHandsParsedEvent } from "#/types/core";
import { AddTaskAction } from "#/types/core/actions";
import { BrowseObservation } from "#/types/core/observations";

const HOST = "localhost:3000";

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

const INITIAL_PARSED_DATA_STATE: ParsedData = {
  messages: [],
  terminalStreams: [],
  jupyterCells: [],
  browseState: null,
  taskState: null,
  agentState: "loading",
};

type ReinitializeSessionConfig = {
  resetToken: boolean;
};

interface SessionContextType {
  reinitializeSession: (config: ReinitializeSessionConfig) => void;
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
  const { socket, initializeWebSocket } = useWebSocket(HOST);
  const [eventLog, setEventLog] = React.useState<string[]>([]);

  // parsed data that is used throughout the app
  const [data, setData] = React.useState<ParsedData>(INITIAL_PARSED_DATA_STATE);

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

  /**
   * Initialize the agent by sending an agent init event. Uses current settings.
   */
  const initializeAgent = () => {
    const event = generateAgentInitEvent();
    socket?.send(event);
  };

  const reinitializeSession = ({
    resetToken = true,
  }: ReinitializeSessionConfig) => {
    initializeWebSocket(resetToken);
  };

  React.useEffect(() => {
    if (socket) {
      socket.onopen = () => {
        initializeAgent();
      };

      socket.onmessage = (event) => {
        pushToEventLog(event.data);
        const message = JSON.parse(event.data) as OpenHandsParsedEvent;

        /** HANDLE EVENT DATA */

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
            agentState: message.extras.agent_state,
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

  const clearEventLog = () => {
    setEventLog([]);
    setData(INITIAL_PARSED_DATA_STATE);
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
   * Send a change in agent state to the assistant. If the agent state is "stopped", a new session is started.
   * @param agent_state The new agent state
   */
  const triggerAgentStateChange = (agent_state: AgentState) => {
    const event = generateAgentStateChangeEvent(agent_state);
    sendMessageToSocket(event);
    if (agent_state === "stopped") {
      clearEventLog();
      reinitializeSession({ resetToken: true });
    }
  };

  const value = React.useMemo(
    () => ({
      reinitializeSession,
      sendUserMessage,
      sendTerminalCommand,
      triggerAgentStateChange,
      eventLog,
      data,
    }),
    [
      reinitializeSession,
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
