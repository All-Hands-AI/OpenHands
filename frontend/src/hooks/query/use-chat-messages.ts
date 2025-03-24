import { useQueryClient } from "@tanstack/react-query";
import type { Message } from "#/message";

// Query key for chat messages
const CHAT_MESSAGES_QUERY_KEY = ["_STATE", "chat", "messages"];

/**
 * Sets the chat messages in the query cache
 * @param queryClient - The React Query client
 * @param messages - The messages to set
 */
export function setChatMessages(
  queryClient: ReturnType<typeof useQueryClient>,
  messages: Message[],
) {
  console.log("Setting chat messages:", messages);
  queryClient.setQueryData(CHAT_MESSAGES_QUERY_KEY, messages);
}

/**
 * Adds a user message to the chat
 * @param queryClient - The React Query client
 * @param payload - The message payload
 */
export function addUserMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  },
) {
  console.log("Adding user message:", payload);
  const messages =
    queryClient.getQueryData<Message[]>(CHAT_MESSAGES_QUERY_KEY) || [];
  console.log("Current messages before adding user message:", messages);

  const message: Message = {
    type: "thought",
    sender: "user",
    content: payload.content,
    imageUrls: payload.imageUrls,
    timestamp: payload.timestamp || new Date().toISOString(),
    pending: !!payload.pending,
  };

  // Remove any pending messages
  const filteredMessages = messages.filter((m) => !m.pending);

  // Set the updated messages
  setChatMessages(queryClient, [...filteredMessages, message]);
}

/**
 * Adds an assistant message to the chat
 * @param queryClient - The React Query client
 * @param content - The message content
 */
export function addAssistantMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  content: string,
) {
  console.log("Adding assistant message:", content);
  const messages =
    queryClient.getQueryData<Message[]>(CHAT_MESSAGES_QUERY_KEY) || [];
  console.log("Current messages before adding assistant message:", messages);

  const message: Message = {
    type: "thought",
    sender: "assistant",
    content,
    imageUrls: [],
    timestamp: new Date().toISOString(),
    pending: false,
  };

  setChatMessages(queryClient, [...messages, message]);
}

/**
 * Adds an error message to the chat
 * @param queryClient - The React Query client
 * @param payload - The error message payload
 */
export function addErrorMessage(
  queryClient: ReturnType<typeof useQueryClient>,
  payload: { id?: string; message: string },
) {
  const messages =
    queryClient.getQueryData<Message[]>(CHAT_MESSAGES_QUERY_KEY) || [];

  const message: Message = {
    translationID: payload.id,
    content: payload.message,
    type: "error",
    sender: "assistant",
    timestamp: new Date().toISOString(),
  };

  setChatMessages(queryClient, [...messages, message]);
}

/**
 * Clears all chat messages
 * @param queryClient - The React Query client
 */
export function clearMessages(queryClient: ReturnType<typeof useQueryClient>) {
  setChatMessages(queryClient, []);
}

/**
 * Hook to access and manage chat messages
 * @returns Object containing the messages and message management functions
 */
export function useChatMessages(): {
  messages: Message[];
  addUserMessage: (payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  }) => void;
  addAssistantMessage: (content: string) => void;
  addErrorMessage: (payload: { id?: string; message: string }) => void;
  clearMessages: () => void;
} {
  const queryClient = useQueryClient();

  // Get the current messages from the query cache
  const messages =
    queryClient.getQueryData<Message[]>(CHAT_MESSAGES_QUERY_KEY) || [];
  
  console.log("useChatMessages hook - current messages:", messages);

  // Create setter functions that components can use
  const addUserMessageFn = (payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  }) => {
    console.log("useChatMessages hook - addUserMessage called with:", payload);
    addUserMessage(queryClient, payload);
  };

  const addAssistantMessageFn = (content: string) => {
    console.log("useChatMessages hook - addAssistantMessage called with:", content);
    addAssistantMessage(queryClient, content);
  };

  const addErrorMessageFn = (payload: { id?: string; message: string }) => {
    console.log("useChatMessages hook - addErrorMessage called with:", payload);
    addErrorMessage(queryClient, payload);
  };

  const clearMessagesFn = () => {
    console.log("useChatMessages hook - clearMessages called");
    clearMessages(queryClient);
  };

  return {
    messages,
    addUserMessage: addUserMessageFn,
    addAssistantMessage: addAssistantMessageFn,
    addErrorMessage: addErrorMessageFn,
    clearMessages: clearMessagesFn,
  };
}
