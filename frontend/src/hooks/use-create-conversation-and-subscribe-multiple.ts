import React from "react";
import { useCreateConversation } from "./mutation/use-create-conversation";
import { useUserProviders } from "./use-user-providers";
import { useConversationSubscriptions } from "#/context/conversation-subscriptions-provider";
import { Provider } from "#/types/settings";
import { CreateMicroagent } from "#/api/open-hands.types";

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
          onSuccess: (data) => {
            let baseUrl = "";
            let socketPath: string | undefined = undefined;
            if (data?.url && !data.url.startsWith("/")) {
              const u = new URL(data.url);
              baseUrl = u.host;
              const pathBeforeApi = u.pathname.split("/api/conversations")[0] || "/";
              socketPath = `${pathBeforeApi.replace(/\/$/, "")}/socket.io`;
            } else {
              baseUrl =
                (import.meta.env.VITE_BACKEND_BASE_URL as string | undefined) ||
                window?.location.host;
              socketPath = "/socket.io";
            }

            // Subscribe to the conversation
            subscribeToConversation({
              conversationId: data.conversation_id,
              sessionApiKey: data.session_api_key,
              providersSet: providers,
              baseUrl,
              socketPath,
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
