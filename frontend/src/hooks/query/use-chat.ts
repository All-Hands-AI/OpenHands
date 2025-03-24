import { useQueryClient, useMutation, useQuery } from "@tanstack/react-query";
import { Message } from "#/message";
import { ActionSecurityRisk } from "#/hooks/query/use-security-analyzer";
import {
  OpenHandsObservation,
  CommandObservation,
  IPythonObservation,
} from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";
import { QueryKeys } from "./query-keys";
const MAX_CONTENT_LENGTH = 1000;
const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
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
/**
 * Hook for managing chat messages using React Query
 */
export function useChat() {
  const queryClient = useQueryClient();
  const queryClient = useQueryClient();
    // eslint-disable-next-line no-console
  // Mutation to add a user message
  const addUserMessageMutation = useMutation({
    mutationFn: async (payload: {
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
      const currentState = queryClient.getQueryData<{ messages: Message[] }>([
        "chat",
      ]) || { messages: [] };
      // Remove any pending messages
      const updatedMessages = [...currentState.messages];
      let i = updatedMessages.length;
      while (i) {
        i -= 1;
        const m = updatedMessages[i] as Message;
        if (m.pending) {
          updatedMessages.splice(i, 1);
        }
      // Add the new message
      updatedMessages.push(message);
      // Update the query cache
      queryClient.setQueryData(QueryKeys.chat, { messages: updatedMessages });
          type: "chat/addUserMessage",
          payload,
        });
      return { messages: updatedMessages };
    },
  });
  // Mutation to add an assistant message
  const addAssistantMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      const message: Message = {
        type: "thought",
        sender: "assistant",
        content,
        imageUrls: [],
        timestamp: new Date().toISOString(),
        pending: false,
      };
      const currentState = queryClient.getQueryData<{ messages: Message[] }>([
        "chat",
      ]) || { messages: [] };
      const updatedMessages = [...currentState.messages, message];
      // Update the query cache
      queryClient.setQueryData(QueryKeys.chat, { messages: updatedMessages });
          type: "chat/addAssistantMessage",
          payload: content,
        });
      return { messages: updatedMessages };
    },
  });
  // Mutation to add an assistant action
  const addAssistantActionMutation = useMutation({
    mutationFn: async (action: OpenHandsAction) => {
      const actionID = action.action;
      if (!HANDLED_ACTIONS.includes(actionID)) {
        return (
          queryClient.getQueryData<{ messages: Message[] }>(QueryKeys.chat) || {
            messages: [],
          }
        );
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
      if (actionID === "run" || actionID === "run_ipython") {
        if (action.args.confirmation_state === "awaiting_confirmation") {
          text += `\n\n${getRiskText(
            action.args.security_risk as unknown as ActionSecurityRisk,
          )}`;
        }
      } else if (actionID === "think") {
        text = action.args.thought;
      const message: Message = {
        type: "action",
        sender: "assistant",
        translationID,
        eventID: action.id,
        content: text,
        imageUrls: [],
        timestamp: new Date().toISOString(),
      };
      const currentState = queryClient.getQueryData<{ messages: Message[] }>([
        "chat",
      ]) || { messages: [] };
      const updatedMessages = [...currentState.messages, message];
      // Update the query cache
      queryClient.setQueryData(QueryKeys.chat, { messages: updatedMessages });
          type: "chat/addAssistantAction",
          payload: action,
        });
      return { messages: updatedMessages };
    },
  });
  // Mutation to add an assistant observation
  const addAssistantObservationMutation = useMutation({
    mutationFn: async (observation: OpenHandsObservation) => {
      const observationID = observation.observation;
      if (!HANDLED_ACTIONS.includes(observationID)) {
        return (
          queryClient.getQueryData<{ messages: Message[] }>(QueryKeys.chat) || {
            messages: [],
          }
        );
      const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
      const causeID = observation.cause;
      const currentState = queryClient.getQueryData<{ messages: Message[] }>([
        "chat",
      ]) || { messages: [] };
      const updatedMessages = [...currentState.messages];
      const causeMessageIndex = updatedMessages.findIndex(
        (message) => message.eventID === causeID,
      );
      if (causeMessageIndex === -1) {
        return { messages: updatedMessages };
      const causeMessage = { ...updatedMessages[causeMessageIndex] };
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
      updatedMessages[causeMessageIndex] = causeMessage;
      // Update the query cache
      queryClient.setQueryData(QueryKeys.chat, { messages: updatedMessages });
          type: "chat/addAssistantObservation",
          payload: observation,
        });
      return { messages: updatedMessages };
    },
  });
  // Mutation to add an error message
  const addErrorMessageMutation = useMutation({
    mutationFn: async (payload: { id?: string; message: string }) => {
      const { id, message } = payload;
      const errorMessage: Message = {
        translationID: id,
        content: message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      };
      const currentState = queryClient.getQueryData<{ messages: Message[] }>([
        "chat",
      ]) || { messages: [] };
      const updatedMessages = [...currentState.messages, errorMessage];
      // Update the query cache
      queryClient.setQueryData(QueryKeys.chat, { messages: updatedMessages });
          type: "chat/addErrorMessage",
          payload,
        });
      return { messages: updatedMessages };
    },
  });
  // Mutation to clear all messages
  const clearMessagesMutation = useMutation({
    mutationFn: async () => {
      // Update the query cache
      queryClient.setQueryData(QueryKeys.chat, { messages: [] });
          type: "chat/clearMessages",
        });
      return { messages: [] };
    },
  });
  return {
    messages: query.data?.messages || [],
    isLoading: query.isLoading,
    addUserMessage: addUserMessageMutation.mutate,
    addAssistantMessage: addAssistantMessageMutation.mutate,
    addAssistantAction: addAssistantActionMutation.mutate,
    addAssistantObservation: addAssistantObservationMutation.mutate,
    addErrorMessage: addErrorMessageMutation.mutate,
    clearMessages: clearMessagesMutation.mutate,
  };
}
