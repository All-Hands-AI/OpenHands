import React from "react";
import { useQueries, type Query } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Spinner } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { useCreateConversation } from "./mutation/use-create-conversation";
import { useUserProviders } from "./use-user-providers";
import { useConversationSubscriptions } from "#/context/conversation-subscriptions-provider";
import { Provider } from "#/types/settings";
import { CreateMicroagent, Conversation } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";
import CloseIcon from "#/icons/close.svg?react";
import { AxiosError } from "axios";

interface ConversationData {
  conversationId: string;
  sessionApiKey: string | null;
  baseUrl: string;
  onEventCallback?: (event: unknown, conversationId: string) => void;
}

interface ConversationStartingToastProps {
  conversationId: string;
  onClose: () => void;
}

function ConversationStartingToast({
  conversationId,
  onClose,
}: ConversationStartingToastProps) {
  const { t } = useTranslation();
  return (
    <div className="flex items-start gap-2">
      <Spinner size="sm" />
      <div>
        {t("MICROAGENT$CONVERSATION_STARTING")}
        <br />
        <a
          href={`/conversations/${conversationId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          {t("MICROAGENT$VIEW_CONVERSATION")}
        </a>
      </div>
      <button type="button" onClick={onClose}>
        <CloseIcon />
      </button>
    </div>
  );
}

const renderConversationStartingToast = (conversationId: string) =>
  toast(
    (toastInstance) => (
      <ConversationStartingToast
        conversationId={conversationId}
        onClose={() => toast.dismiss(toastInstance.id)}
      />
    ),
    {
      ...TOAST_OPTIONS,
      id: `starting-${conversationId}`,
      duration: 10000, // Show for 10 seconds or until dismissed
    },
  );

/**
 * Custom hook to create a conversation and subscribe to it, supporting multiple subscriptions.
 * This version waits for conversation status to be "RUNNING" before establishing WebSocket connection.
 * Shows immediate toast feedback and polls conversation status until ready.
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

  // Store conversation data immediately after creation
  const [createdConversations, setCreatedConversations] = React.useState<
    Record<string, ConversationData>
  >({});

  // Get conversation IDs that need polling
  const conversationIdsToWatch = Object.keys(createdConversations);

  // Poll each conversation until it's ready
  const conversationQueries = useQueries({
    queries: conversationIdsToWatch.map((conversationId) => ({
      queryKey: ["conversation-ready-poll", conversationId],
      queryFn: () => OpenHands.getConversation(conversationId),
      enabled: !!conversationId,
      refetchInterval: (query: Query<Conversation | null, AxiosError>) => {
        const status = query.state.data?.status;
        if (status === "STARTING") {
          return 3000; // Poll every 3 seconds while STARTING
        }
        return false; // Stop polling once not STARTING
      },
      retry: false,
    })),
  });

  // Effect to handle subscription when conversations are ready
  React.useEffect(() => {
    conversationQueries.forEach((query, index) => {
      const conversationId = conversationIdsToWatch[index];
      const conversationData = createdConversations[conversationId];

      if (!query.data || !conversationData) return;

      const { status } = query.data;

      if (status === "RUNNING") {
        // Conversation is ready - subscribe to WebSocket
        subscribeToConversation({
          conversationId: conversationData.conversationId,
          sessionApiKey: conversationData.sessionApiKey,
          providersSet: providers,
          baseUrl: conversationData.baseUrl,
          onEvent: conversationData.onEventCallback,
        });

        // Remove from created conversations (cleanup)
        setCreatedConversations((prev) => {
          const newCreated = { ...prev };
          delete newCreated[conversationId];
          return newCreated;
        });
      } else if (status === "STOPPED") {
        // Dismiss the starting toast
        toast.dismiss(`starting-${conversationId}`);

        // Conversation failed to start
        console.warn(
          `Conversation ${conversationId} stopped before WebSocket connection could be established`,
        );

        // Remove from created conversations (cleanup)
        setCreatedConversations((prev) => {
          const newCreated = { ...prev };
          delete newCreated[conversationId];
          return newCreated;
        });
      }
    });
  }, [
    conversationQueries,
    createdConversations,
    subscribeToConversation,
    providers,
  ]);

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
            // Show immediate toast to let user know something is happening
            renderConversationStartingToast(data.conversation_id);

            // Call the success callback immediately
            if (onSuccessCallback) {
              onSuccessCallback(data.conversation_id);
            }

            // Only handle immediate post-creation tasks here
            let baseUrl = "";
            if (data?.url && !data.url.startsWith("/")) {
              baseUrl = new URL(data.url).host;
            } else {
              baseUrl =
                (import.meta.env.VITE_BACKEND_BASE_URL as string | undefined) ||
                window?.location.host;
            }

            // Store conversation data for polling and eventual subscription
            setCreatedConversations((prev) => ({
              ...prev,
              [data.conversation_id]: {
                conversationId: data.conversation_id,
                sessionApiKey: data.session_api_key,
                baseUrl,
                onEventCallback,
              },
            }));
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
