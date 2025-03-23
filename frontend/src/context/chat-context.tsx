import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
} from "react";
import type { Message } from "#/message";
import {
  OpenHandsObservation,
  CommandObservation,
  IPythonObservation,
} from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";

// Constants
const MAX_CONTENT_LENGTH = 1000;

const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
  "edit",
];

// Helper functions
function getRiskText(risk: ActionSecurityRisk) {
  switch (risk) {
    case ActionSecurityRisk.LOW:
      return "Low Risk";
    case ActionSecurityRisk.MEDIUM:
      return "Medium Risk";
    case ActionSecurityRisk.HIGH:
      return "High Risk";
    case ActionSecurityRisk.UNKNOWN:
    default:
      return "Unknown Risk";
  }
}

// Context type definition
type ChatContextType = {
  messages: Message[];
  addUserMessage: (payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  }) => void;
  addAssistantMessage: (content: string) => void;
  addAssistantAction: (action: OpenHandsAction) => void;
  addAssistantObservation: (observation: OpenHandsObservation) => void;
  addErrorMessage: (payload: { id?: string; message: string }) => void;
  clearMessages: () => void;
};

// Create context with default values
const ChatContext = createContext<ChatContextType>({
  messages: [],
  addUserMessage: () => {},
  addAssistantMessage: () => {},
  addAssistantAction: () => {},
  addAssistantObservation: () => {},
  addErrorMessage: () => {},
  clearMessages: () => {},
});

// Provider component
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);

  // Define all the functions first
  const addUserMessage = useCallback(
    (payload: {
      content: string;
      imageUrls: string[];
      timestamp: string;
      pending?: boolean;
    }) => {
      const message: Message = {
        type: "thought",
        sender: "user",
        content: payload.content,
        imageUrls: payload.imageUrls,
        timestamp: payload.timestamp || new Date().toISOString(),
        pending: !!payload.pending,
      };

      setMessages((prevMessages) => {
        // Remove any pending messages
        const filteredMessages = prevMessages.filter((m) => !m.pending);
        return [...filteredMessages, message];
      });
    },
    [],
  );

  const addAssistantMessage = useCallback((content: string) => {
    const message: Message = {
      type: "thought",
      sender: "assistant",
      content,
      imageUrls: [],
      timestamp: new Date().toISOString(),
      pending: false,
    };

    setMessages((prevMessages) => [...prevMessages, message]);
  }, []);

  const addAssistantAction = useCallback((action: OpenHandsAction) => {
    const actionID = action.action;
    if (!HANDLED_ACTIONS.includes(actionID)) {
      return;
    }

    const translationID = `ACTION_MESSAGE$${actionID.toUpperCase()}`;
    let text = "";

    if (actionID === "run") {
      text = `Command:\n\`${action.args.command}\``;
    } else if (actionID === "run_ipython") {
      text = `\`\`\`\n${action.args.code}\n\`\`\``;
    } else if (actionID === "write") {
      let { content } = action.args;
      if (content.length > MAX_CONTENT_LENGTH) {
        content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
      }
      text = `${action.args.path}\n${content}`;
    } else if (actionID === "browse") {
      text = `Browsing ${action.args.url}`;
    }

    if (actionID === "run" || actionID === "run_ipython") {
      if (action.args.confirmation_state === "awaiting_confirmation") {
        text += `\n\n${getRiskText(
          action.args.security_risk as unknown as ActionSecurityRisk,
        )}`;
      }
    } else if (actionID === "think") {
      text = action.args.thought;
    }

    const message: Message = {
      type: "action",
      sender: "assistant",
      translationID,
      eventID: action.id,
      content: text,
      imageUrls: [],
      timestamp: new Date().toISOString(),
    };

    setMessages((prevMessages) => [...prevMessages, message]);
  }, []);

  const addAssistantObservation = useCallback(
    (observation: OpenHandsObservation) => {
      const observationID = observation.observation;
      if (!HANDLED_ACTIONS.includes(observationID)) {
        return;
      }

      const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
      const causeID = observation.cause;

      setMessages((prevMessages) => {
        // Find the message that caused this observation
        const messageIndex = prevMessages.findIndex(
          (message) => message.eventID === causeID,
        );

        if (messageIndex === -1) {
          return prevMessages;
        }

        // Create a copy of the messages array
        const updatedMessages = [...prevMessages];
        const causeMessage = { ...updatedMessages[messageIndex] };

        // Update the cause message
        causeMessage.translationID = translationID;

        // Set success property based on observation type
        if (observationID === "run") {
          const commandObs = observation as CommandObservation;
          causeMessage.success = commandObs.extras.metadata.exit_code === 0;
        } else if (observationID === "run_ipython") {
          // For IPython, we consider it successful if there's no error message
          const ipythonObs = observation as IPythonObservation;
          causeMessage.success = !ipythonObs.content
            .toLowerCase()
            .includes("error:");
        } else if (observationID === "read" || observationID === "edit") {
          // For read/edit operations, we consider it successful if there's content and no error
          if (observation.extras.impl_source === "oh_aci") {
            causeMessage.success =
              observation.content.length > 0 &&
              !observation.content.startsWith("ERROR:\n");
          } else {
            causeMessage.success =
              observation.content.length > 0 &&
              !observation.content.toLowerCase().includes("error:");
          }
        }

        // Update content based on observation type
        if (observationID === "run" || observationID === "run_ipython") {
          let { content } = observation;
          if (content.length > MAX_CONTENT_LENGTH) {
            content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
          }
          content = `${
            causeMessage.content
          }\n\nOutput:\n\`\`\`\n${content.trim() || "[Command finished execution with no output]"}\n\`\`\``;
          causeMessage.content = content; // Observation content includes the action
        } else if (observationID === "read") {
          causeMessage.content = `\`\`\`\n${observation.content}\n\`\`\``; // Content is already truncated by the ACI
        } else if (observationID === "edit") {
          if (causeMessage.success) {
            causeMessage.content = `\`\`\`diff\n${observation.extras.diff}\n\`\`\``; // Content is already truncated by the ACI
          } else {
            causeMessage.content = observation.content;
          }
        } else if (observationID === "browse") {
          let content = `**URL:** ${observation.extras.url}\n`;
          if (observation.extras.error) {
            content += `**Error:**\n${observation.extras.error}\n`;
          }
          content += `**Output:**\n${observation.content}`;
          if (content.length > MAX_CONTENT_LENGTH) {
            content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
          }
          causeMessage.content = content;
        }

        // Replace the old message with the updated one
        updatedMessages[messageIndex] = causeMessage;
        return updatedMessages;
      });
    },
    [],
  );

  const addErrorMessage = useCallback(
    (payload: { id?: string; message: string }) => {
      const { id, message } = payload;
      const errorMessage: Message = {
        translationID: id,
        content: message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      };

      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    },
    [],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Register the functions with the chat service
  React.useEffect(() => {
    import("#/services/context-services/chat-service").then(
      ({ registerChatFunctions }) => {
        registerChatFunctions({
          addUserMessage,
          addAssistantMessage,
          addAssistantAction,
          addAssistantObservation,
          addErrorMessage,
          clearMessages,
          getMessages: () => messages,
        });
      },
    );
  }, [
    addUserMessage,
    addAssistantMessage,
    addAssistantAction,
    addAssistantObservation,
    addErrorMessage,
    clearMessages,
    messages,
  ]);

  // Create a memoized context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    () => ({
      messages,
      addUserMessage,
      addAssistantMessage,
      addAssistantAction,
      addAssistantObservation,
      addErrorMessage,
      clearMessages,
    }),
    [
      messages,
      addUserMessage,
      addAssistantMessage,
      addAssistantAction,
      addAssistantObservation,
      addErrorMessage,
      clearMessages,
    ],
  );

  return (
    <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>
  );
}

// Custom hook to use the chat context
export function useChatContext() {
  const context = useContext(ChatContext);

  if (context === undefined) {
    throw new Error("useChatContext must be used within a ChatProvider");
  }

  return context;
}
