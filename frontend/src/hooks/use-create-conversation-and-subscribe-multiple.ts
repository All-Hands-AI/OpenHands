import React from "react";
import { useCreateConversation } from "./mutation/use-create-conversation";
import { useUserProviders } from "./use-user-providers";
import { useConversationSubscriptions } from "#/context/conversation-subscriptions-provider";
import { Provider } from "#/types/settings";

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
      onSuccessCallback?: (conversationId: string) => void;
      onEventCallback?: (event: unknown, conversationId: string) => void;
    }) => {
      createConversation(
        {
          query,
          conversationInstructions,
          repository,
        },
        {
          onSuccess: (data) => {
            let baseUrl = "";
            if (data?.url && !data.url.startsWith("/")) {
              baseUrl = new URL(data.url).host;
            } else {
              baseUrl =
                (import.meta.env.VITE_BACKEND_BASE_URL as string | undefined) ||
                window?.location.host;
            }

            // Subscribe to the conversation
            subscribeToConversation({
              conversationId: data.conversation_id,
              sessionApiKey: data.session_api_key,
              providersSet: providers,
              baseUrl,
              onEvent: onEventCallback,
            });

            // Call the success callback if provided
            if (onSuccessCallback) {
              onSuccessCallback(data.conversation_id);
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
