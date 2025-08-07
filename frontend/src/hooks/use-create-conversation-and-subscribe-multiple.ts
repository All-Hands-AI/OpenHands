import React from "react";
import { useCreateConversation } from "./mutation/use-create-conversation";
import { useUserProviders } from "./use-user-providers";
import { useConversationSubscriptions } from "#/context/conversation-subscriptions-provider";
import { Provider } from "#/types/settings";
import { CreateMicroagent } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";

/**
 * Custom hook to create a conversation and subscribe to it, supporting multiple subscriptions.
 * This extends the functionality of useCreateConversationAndSubscribe to allow subscribing to
 * multiple conversations simultaneously.
 */
export const useCreateConversationAndSubscribeMultiple = () => {
  const { mutate: createConversation, isPending } = useCreateConversation();
  const { providers } = useUserProviders();
  const {
    subscribeToConversation,
    unsubscribeFromConversation,
    isSubscribedToConversation,
    activeConversationIds,
  } = useConversationSubscriptions();

  const createConversationAndSubscribe = React.useCallback(
    ({
      query,
      conversationInstructions,
      repository,
      createMicroagent,
      onSuccessCallback,
      onEventCallback,
    }: {
      query: string;
      conversationInstructions: string;
      repository: {
        name: string;
        branch: string;
        gitProvider: Provider;
      };
      createMicroagent?: CreateMicroagent;
      onSuccessCallback?: (conversationId: string) => void;
      onEventCallback?: (event: unknown, conversationId: string) => void;
    }) => {
      createConversation(
        {
          query,
          conversationInstructions,
          repository,
          createMicroagent,
        },
        {
          onSuccess: async (data) => {
            try {
              // NOTE: createConversation returns ConversationResponse (no url/session_api_key)
              // but we need the full Conversation object for WebSocket connection.
              // Wait for conversation to be fully loaded to get proper url and session_api_key
              const conversation = await OpenHands.getConversation(
                data.conversation_id,
              );
              if (!conversation) {
                // eslint-disable-next-line no-console
                console.error("Failed to load conversation after creation");
                return;
              }

              let baseUrl = "";
              if (conversation.url && !conversation.url.startsWith("/")) {
                baseUrl = new URL(conversation.url).host;
              } else {
                baseUrl =
                  (import.meta.env.VITE_BACKEND_BASE_URL as
                    | string
                    | undefined) || window?.location.host;
              }

              // Subscribe to the conversation using the loaded conversation data
              subscribeToConversation({
                conversationId: conversation.conversation_id,
                sessionApiKey: conversation.session_api_key,
                providersSet: providers,
                baseUrl,
                onEvent: onEventCallback,
              });

              // Call the success callback if provided
              if (onSuccessCallback) {
                onSuccessCallback(data.conversation_id);
              }
            } catch (error) {
              // eslint-disable-next-line no-console
              console.error(
                "Error loading conversation for WebSocket connection:",
                error,
              );
              // Fallback to original behavior if fetching conversation fails
              let baseUrl = "";
              if (data?.url && !data.url.startsWith("/")) {
                baseUrl = new URL(data.url).host;
              } else {
                baseUrl =
                  (import.meta.env.VITE_BACKEND_BASE_URL as
                    | string
                    | undefined) || window?.location.host;
              }

              subscribeToConversation({
                conversationId: data.conversation_id,
                sessionApiKey: data.session_api_key,
                providersSet: providers,
                baseUrl,
                onEvent: onEventCallback,
              });

              if (onSuccessCallback) {
                onSuccessCallback(data.conversation_id);
              }
            }
          },
        },
      );
    },
    [createConversation, subscribeToConversation, providers],
  );

  return {
    createConversationAndSubscribe,
    unsubscribeFromConversation,
    isSubscribedToConversation,
    activeConversationIds,
    isPending,
  };
};
