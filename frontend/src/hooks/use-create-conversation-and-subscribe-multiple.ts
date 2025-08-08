import React from "react";
import toast from "react-hot-toast";
import { useCreateConversation } from "./mutation/use-create-conversation";
import { useConversationSubscriptions } from "#/context/conversation-subscriptions-provider";
import { Provider } from "#/types/settings";
import { CreateMicroagent } from "#/api/open-hands.types";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";
import OpenHands from "#/api/open-hands";

/**
 * Custom hook to create a conversation and subscribe to it, supporting multiple subscriptions.
 * This extends the functionality of useCreateConversationAndSubscribe to allow subscribing to
 * multiple conversations simultaneously.
 */

export const useCreateConversationAndSubscribeMultiple = () => {
  const { mutate: createConversation, isPending } = useCreateConversation();
  const {
    unsubscribeFromConversation,
    isSubscribedToConversation,
    activeConversationIds,
    subscribeToConversation,
  } = useConversationSubscriptions();

  // Track conversations that are being set up with their callbacks
  const [pendingConversations, setPendingConversations] = React.useState<
    Map<
      string,
      {
        onEventCallback?: (event: unknown, conversationId: string) => void;
        repositoryName: string;
      }
    >
  >(new Map());

  // Handle polling and subscription for pending conversations
  React.useEffect(() => {
    const handleConversationPolling = async () => {
      const conversationsToProcess = Array.from(pendingConversations.entries());

      await Promise.all(
        conversationsToProcess.map(async ([conversationId, config]) => {
          try {
            const conversation =
              await OpenHands.getConversation(conversationId);

            if (
              conversation?.status === "RUNNING" &&
              conversation.runtime_status
            ) {
              // Conversation is ready, subscribe to it
              let baseUrl = "";
              if (conversation.url && !conversation.url.startsWith("/")) {
                baseUrl = new URL(conversation.url).host;
              } else {
                baseUrl =
                  (import.meta.env.VITE_BACKEND_BASE_URL as
                    | string
                    | undefined) || window?.location.host;
              }

              subscribeToConversation({
                conversationId,
                sessionApiKey: conversation.session_api_key,
                providersSet: [], // Empty array since we don't need providers for subscription
                baseUrl,
                onEvent: config.onEventCallback,
              });

              // Remove from pending when subscription is established
              setPendingConversations((prev) => {
                const newMap = new Map(prev);
                newMap.delete(conversationId);
                return newMap;
              });
            }
          } catch (error) {
            // Remove failed conversation from pending
            setPendingConversations((prev) => {
              const newMap = new Map(prev);
              newMap.delete(conversationId);
              return newMap;
            });
          }
        }),
      );
    };

    if (pendingConversations.size > 0) {
      const interval = setInterval(handleConversationPolling, 1000);
      return () => clearInterval(interval);
    }
    return undefined;
  }, [pendingConversations, subscribeToConversation]);

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
            // Add to pending conversations for polling
            setPendingConversations((prev) => {
              const newMap = new Map(prev);
              newMap.set(data.conversation_id, {
                onEventCallback,
                repositoryName: repository.name,
              });
              return newMap;
            });

            // Show immediate "starting" toast to give user feedback
            toast(`Starting conversation for ${repository.name}...`, {
              ...TOAST_OPTIONS,
              id: `starting-${data.conversation_id}`,
              duration: 10000, // Longer duration since this will be replaced by the runtime status toast
            });

            // Call the success callback immediately (conversation created)
            if (onSuccessCallback) {
              onSuccessCallback(data.conversation_id);
            }
          },
        },
      );
    },
    [createConversation],
  );

  return {
    createConversationAndSubscribe,
    unsubscribeFromConversation,
    isSubscribedToConversation,
    activeConversationIds,
    isPending,
  };
};
