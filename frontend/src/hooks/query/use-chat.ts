import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import type { Message } from "#/message";
import { ActionSecurityRisk } from "#/types/migrated-types";
import {
  OpenHandsObservation,
  CommandObservation,
  IPythonObservation,
} from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";

// Constants from the original chat slice
const MAX_CONTENT_LENGTH = 1000;

const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
  "edit",
];

// Helper function from the original chat slice
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

/**
 * Hook to access and manipulate chat messages using React Query
 * This replaces the Redux chat slice functionality
 */
export function useChat() {
  console.log("[DOUBLE_MSG_DEBUG] useChat hook initializing", {
    timestamp: new Date().toISOString()
  });
  
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    console.warn(
      "QueryReduxBridge not initialized, using default chat messages",
    );
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialMessages = (): Message[] => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<Message[]>([
      "chat",
      "messages",
    ]);

    console.log("[useChat Debug] getInitialMessages:", {
      hasExistingData: !!existingData,
      existingDataLength: existingData?.length || 0,
      hasBridge: !!bridge,
    });

    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        const reduxMessages = bridge.getReduxSliceState<{
          messages: Message[];
        }>("chat").messages;
        console.log("[useChat Debug] Got messages from Redux:", {
          count: reduxMessages.length,
          messages: reduxMessages.map((m) => ({
            type: m.type,
            sender: m.sender,
            content: m.content
              ? m.content.substring(0, 30) +
                (m.content.length > 30 ? "..." : "")
              : "",
          })),
        });
        return reduxMessages;
      } catch (error) {
        console.log(
          "[useChat Debug] Error getting messages from Redux:",
          error,
        );
        // If we can't get the state from Redux, return the initial state
        return [];
      }
    }

    // If bridge is not available, return the initial state
    console.log("[useChat Debug] Bridge not available, returning empty array");
    return [];
  };

  // Query for chat messages
  const query = useQuery({
    queryKey: ["chat", "messages"],
    queryFn: () => getInitialMessages(),
    initialData: getInitialMessages,
    staleTime: Infinity, // We manage updates manually through mutations
  });

  // Mutation to add a user message
  const addUserMessageMutation = useMutation({
    mutationFn: (payload: {
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
      return Promise.resolve(message);
    },
    onMutate: async (payload) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });

      // Get current messages
      const previousMessages =
        queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

      // Create new message
      const message: Message = {
        type: "thought",
        sender: "user",
        content: payload.content,
        imageUrls: payload.imageUrls,
        timestamp: payload.timestamp || new Date().toISOString(),
        pending: !!payload.pending,
      };

      // Remove any pending messages
      const filteredMessages = previousMessages.filter((m) => !m.pending);

      // Log before updating messages
      console.log("[DOUBLE_MSG_DEBUG] addUserMessageMutation updating query cache:", {
        messageId: `user-${message.timestamp}`,
        content: message.content.substring(0, 30) + (message.content.length > 30 ? "..." : ""),
        currentMessagesCount: filteredMessages.length,
        newMessagesCount: filteredMessages.length + 1,
        timestamp: new Date().toISOString()
      });
      
      // Update messages
      queryClient.setQueryData(
        ["chat", "messages"],
        [...filteredMessages, message],
      );

      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ["chat", "messages"],
          context.previousMessages,
        );
      }
    },
  });

  // Mutation to add an assistant message
  const addAssistantMessageMutation = useMutation({
    mutationFn: (content: string) => {
      const message: Message = {
        type: "thought",
        sender: "assistant",
        content,
        imageUrls: [],
        timestamp: new Date().toISOString(),
        pending: false,
      };
      return Promise.resolve(message);
    },
    onMutate: async (content) => {
      console.log("[DOUBLE_MSG_DEBUG] addAssistantMessageMutation.onMutate:", {
        content: content.substring(0, 30) + (content.length > 30 ? "..." : ""),
        timestamp: new Date().toISOString()
      });
      
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });

      // Get current messages
      const previousMessages =
        queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

      // Create new message
      const message: Message = {
        type: "thought",
        sender: "assistant",
        content,
        imageUrls: [],
        timestamp: new Date().toISOString(),
        pending: false,
      };

      // Update messages
      queryClient.setQueryData(
        ["chat", "messages"],
        [...previousMessages, message],
      );

      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ["chat", "messages"],
          context.previousMessages,
        );
      }
    },
  });

  // Mutation to add an assistant action
  const addAssistantActionMutation = useMutation({
    mutationFn: (action: OpenHandsAction) => Promise.resolve(action),
    onMutate: async (action) => {
      const actionID = action.action;
      if (!HANDLED_ACTIONS.includes(actionID)) {
        return { skip: true };
      }

      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });

      // Get current messages
      const previousMessages =
        queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

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

      // Update messages
      queryClient.setQueryData(
        ["chat", "messages"],
        [...previousMessages, message],
      );

      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ["chat", "messages"],
          context.previousMessages,
        );
      }
    },
  });

  // Mutation to add an assistant observation
  const addAssistantObservationMutation = useMutation({
    mutationFn: (observation: OpenHandsObservation) =>
      Promise.resolve(observation),
    onMutate: async (observation) => {
      const observationID = observation.observation;
      if (!HANDLED_ACTIONS.includes(observationID)) {
        return { skip: true };
      }

      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });

      // Get current messages
      const previousMessages =
        queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

      const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
      const causeID = observation.cause;
      const causeMessageIndex = previousMessages.findIndex(
        (message) => message.eventID === causeID,
      );

      if (causeMessageIndex === -1) {
        return { skip: true };
      }

      // Create a deep copy of the messages array
      const updatedMessages = [...previousMessages];
      const causeMessage = { ...updatedMessages[causeMessageIndex] };
      updatedMessages[causeMessageIndex] = causeMessage;

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

      // Update messages
      queryClient.setQueryData(["chat", "messages"], updatedMessages);

      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ["chat", "messages"],
          context.previousMessages,
        );
      }
    },
  });

  // Mutation to add an error message
  const addErrorMessageMutation = useMutation({
    mutationFn: (payload: { id?: string; message: string }) =>
      Promise.resolve(payload),
    onMutate: async (payload) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });

      // Get current messages
      const previousMessages =
        queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

      const { id, message } = payload;
      const errorMessage: Message = {
        translationID: id,
        content: message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      };

      // Update messages
      queryClient.setQueryData(
        ["chat", "messages"],
        [...previousMessages, errorMessage],
      );

      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ["chat", "messages"],
          context.previousMessages,
        );
      }
    },
  });

  // Mutation to clear messages
  const clearMessagesMutation = useMutation({
    mutationFn: () => Promise.resolve(),
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });

      // Get current messages
      const previousMessages =
        queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];

      // Clear messages
      queryClient.setQueryData(["chat", "messages"], []);

      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ["chat", "messages"],
          context.previousMessages,
        );
      }
    },
  });

  // Add debug logging for messages
  const messages = query.data || [];
  console.log("[DOUBLE_MSG_DEBUG] useChat hook returning messages:", {
    count: messages.length,
    messages: messages.map((m) => ({
      type: m.type,
      sender: m.sender,
      content: m.content
        ? m.content.substring(0, 30) + (m.content.length > 30 ? "..." : "")
        : "",
      timestamp: m.timestamp,
    })),
    timestamp: new Date().toISOString()
  });

  return {
    messages,
    isLoading: query.isLoading,
    addUserMessage: (payload: {
      content: string;
      imageUrls: string[];
      timestamp: string;
      pending?: boolean;
    }) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addUserMessage called:", {
        messageId: `user-${payload.timestamp}`,
        content: payload.content.substring(0, 30) + (payload.content.length > 30 ? "..." : ""),
        timestamp: new Date().toISOString()
      });
      addUserMessageMutation.mutate(payload);
    },
    addAssistantMessage: (content: string) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addAssistantMessage called:", {
        content: content.substring(0, 30) + (content.length > 30 ? "..." : ""),
        timestamp: new Date().toISOString()
      });
      addAssistantMessageMutation.mutate(content);
    },
    addAssistantAction: (action: {
      id: string;
      action: string;
      args: Record<string, unknown>;
    }) => {
      console.log("[useChat Debug] Adding assistant action:", {
        id: action.id,
        action: action.action,
        args: action.args,
      });
      // Instead of trying to convert to OpenHandsAction, just pass the action as is
      // and let the middleware handle it
      // We need to use any here because the types don't match exactly
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      addAssistantActionMutation.mutate(action as any);
    },
    addAssistantObservation: (observation: {
      id: string;
      observation: string;
      cause: string;
      content?: string;
      extras?: Record<string, unknown>;
    }) => {
      console.log("[useChat Debug] Adding assistant observation:", {
        id: observation.id,
        observation: observation.observation,
        cause: observation.cause,
      });
      // Instead of trying to convert to OpenHandsObservation, just pass the observation as is
      // and let the middleware handle it
      // We need to use any here because the types don't match exactly
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      addAssistantObservationMutation.mutate(observation as any);
    },
    addErrorMessage: (payload: { id?: string; message: string }) => {
      console.log("[useChat Debug] Adding error message:", payload);
      addErrorMessageMutation.mutate(payload);
    },
    clearMessages: () => {
      console.log("[useChat Debug] Clearing messages");
      clearMessagesMutation.mutate();
    },
  };
}
