import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import { Message } from "#/message";

/**
 * Hook to access and manipulate chat messages using React Query
 * This replaces the Redux chat slice functionality
 */
export function useChatMessages() {
  const queryClient = useQueryClient();
  const bridge = getQueryReduxBridge();

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialMessages = (): Message[] => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<Message[]>(["chat", "messages"]);
    if (existingData) return existingData;
    
    // Otherwise, get initial data from Redux
    return bridge.getReduxSliceState<{ messages: Message[] }>("chat").messages;
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
      const previousMessages = queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];
      
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
      const filteredMessages = previousMessages.filter(m => !m.pending);
      
      // Add new message
      queryClient.setQueryData(["chat", "messages"], [...filteredMessages, message]);
      
      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(["chat", "messages"], context.previousMessages);
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
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });
      
      // Get current messages
      const previousMessages = queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];
      
      // Create new message
      const message: Message = {
        type: "thought",
        sender: "assistant",
        content,
        imageUrls: [],
        timestamp: new Date().toISOString(),
        pending: false,
      };
      
      // Add new message
      queryClient.setQueryData(["chat", "messages"], [...previousMessages, message]);
      
      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(["chat", "messages"], context.previousMessages);
      }
    },
  });

  // Mutation to add an error message
  const addErrorMessageMutation = useMutation({
    mutationFn: (payload: { id?: string; message: string }) => {
      const message: Message = {
        translationID: payload.id,
        content: payload.message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      };
      
      return Promise.resolve(message);
    },
    onMutate: async (payload) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });
      
      // Get current messages
      const previousMessages = queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];
      
      // Create new message
      const message: Message = {
        translationID: payload.id,
        content: payload.message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      };
      
      // Add new message
      queryClient.setQueryData(["chat", "messages"], [...previousMessages, message]);
      
      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(["chat", "messages"], context.previousMessages);
      }
    },
  });

  // Mutation to clear all messages
  const clearMessagesMutation = useMutation({
    mutationFn: () => Promise.resolve(),
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["chat", "messages"] });
      
      // Get current messages
      const previousMessages = queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];
      
      // Clear messages
      queryClient.setQueryData(["chat", "messages"], []);
      
      return { previousMessages };
    },
    onError: (_, __, context) => {
      // Restore previous messages on error
      if (context?.previousMessages) {
        queryClient.setQueryData(["chat", "messages"], context.previousMessages);
      }
    },
  });

  return {
    messages: query.data || [],
    isLoading: query.isLoading,
    addUserMessage: addUserMessageMutation.mutate,
    addAssistantMessage: addAssistantMessageMutation.mutate,
    addErrorMessage: addErrorMessageMutation.mutate,
    clearMessages: clearMessagesMutation.mutate,
  };
}