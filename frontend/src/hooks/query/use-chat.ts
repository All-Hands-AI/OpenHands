import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Message } from "#/message";
import {
  OpenHandsObservation,
  CommandObservation,
  IPythonObservation,
} from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";

type ChatState = { messages: Message[] };

const MAX_CONTENT_LENGTH = 1000;

const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
  "edit",
];

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

const initialState: ChatState = {
  messages: [],
};

// Define query keys
export const chatKeys = {
  all: ["chat"] as const,
  messages: () => [...chatKeys.all, "messages"] as const,
};

// Custom hook to manage chat messages
export function useChat() {
  const queryClient = useQueryClient();

  // Query to get the current messages
  const query = useQuery({
    queryKey: chatKeys.messages(),
    queryFn: () =>
      // Return the cached value or initial value
      queryClient.getQueryData<ChatState>(chatKeys.messages()) || initialState,
    // Initialize with the default chat state
    initialData: initialState,
  });

  // Helper function to update messages
  const updateMessages = (updater: (state: ChatState) => void) => {
    const currentState = queryClient.getQueryData<ChatState>(
      chatKeys.messages(),
    ) || { ...initialState };
    const newState = { ...currentState };
    updater(newState);
    queryClient.setQueryData(chatKeys.messages(), newState);
    return newState;
  };

  // Add user message mutation
  const addUserMessageMutation = useMutation({
    mutationFn: (payload: {
      content: string;
      imageUrls: string[];
      timestamp: string;
      pending?: boolean;
    }) =>
      Promise.resolve(
        updateMessages((state) => {
          const message: Message = {
            type: "thought",
            sender: "user",
            content: payload.content,
            imageUrls: payload.imageUrls,
            timestamp: payload.timestamp || new Date().toISOString(),
            pending: !!payload.pending,
          };
          // Remove any pending messages
          let i = state.messages.length;
          while (i) {
            i -= 1;
            const m = state.messages[i] as Message;
            if (m.pending) {
              state.messages.splice(i, 1);
            }
          }
          state.messages.push(message);
        }),
      ),
  });

  // Add assistant message mutation
  const addAssistantMessageMutation = useMutation({
    mutationFn: (content: string) =>
      Promise.resolve(
        updateMessages((state) => {
          const message: Message = {
            type: "thought",
            sender: "assistant",
            content,
            imageUrls: [],
            timestamp: new Date().toISOString(),
            pending: false,
          };
          state.messages.push(message);
        }),
      ),
  });

  // Add assistant action mutation
  const addAssistantActionMutation = useMutation({
    mutationFn: (action: OpenHandsAction) =>
      Promise.resolve(
        updateMessages((state) => {
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
              text += `\n\n${getRiskText(action.args.security_risk as unknown as ActionSecurityRisk)}`;
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
          state.messages.push(message);
        }),
      ),
  });

  // Add assistant observation mutation
  const addAssistantObservationMutation = useMutation({
    mutationFn: (observation: OpenHandsObservation) =>
      Promise.resolve(
        updateMessages((state) => {
          const observationID = observation.observation;
          if (!HANDLED_ACTIONS.includes(observationID)) {
            return;
          }
          const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
          const causeID = observation.cause;
          const causeMessage = state.messages.find(
            (message) => message.eventID === causeID,
          );
          if (!causeMessage) {
            return;
          }
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
        }),
      ),
  });

  // Add error message mutation
  const addErrorMessageMutation = useMutation({
    mutationFn: (payload: { id?: string; message: string }) =>
      Promise.resolve(
        updateMessages((state) => {
          const { id, message } = payload;
          state.messages.push({
            translationID: id,
            content: message,
            type: "error",
            sender: "assistant",
            timestamp: new Date().toISOString(),
          });
        }),
      ),
  });

  // Clear messages mutation
  const clearMessagesMutation = useMutation({
    mutationFn: () =>
      Promise.resolve(
        updateMessages((state) => {
          state.messages = [];
        }),
      ),
  });

  return {
    messages: query.data.messages,
    addUserMessage: addUserMessageMutation.mutate,
    addAssistantMessage: addAssistantMessageMutation.mutate,
    addAssistantAction: addAssistantActionMutation.mutate,
    addAssistantObservation: addAssistantObservationMutation.mutate,
    addErrorMessage: addErrorMessageMutation.mutate,
    clearMessages: clearMessagesMutation.mutate,
    isLoading: query.isLoading,
  };
}
