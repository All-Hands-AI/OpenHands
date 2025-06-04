import React from "react";
import {
  renderConversationErroredToast,
  renderConversationCreatedToast,
  renderConversationFinishedToast,
} from "#/components/features/chat/microagent/conversation-created-toast";
import { AgentState } from "#/types/agent-state";
import {
  isOpenHandsEvent,
  isAgentStateChangeObservation,
  isStatusUpdate,
} from "#/types/core/guards";
import { AgentStateChangeObservation } from "#/types/core/observations";
import { useCreateConversation } from "./mutation/use-create-conversation";
import {
  useSubscribeToConversation,
  UseSubscribeToConversationOptions,
} from "./use-subscribe-to-conversation";
import { useUserProviders } from "./use-user-providers";
import { Provider } from "#/types/settings";

const isErrorEvent = (
  event: unknown,
): event is { error: true; message: string } =>
  typeof event === "object" &&
  event !== null &&
  "error" in event &&
  event.error === true &&
  "message" in event &&
  typeof event.message === "string";

const isAgentStatusError = (
  event: unknown,
): event is AgentStateChangeObservation =>
  isOpenHandsEvent(event) &&
  isAgentStateChangeObservation(event) &&
  event.extras.agent_state === AgentState.ERROR;

/**
 * Custom hook to create a conversation and subscribe to it. Used for launching
 * microagents and subscribing to their events.
 * @returns
 */
export const useCreateConversationAndSubscribe = () => {
  const { mutate: createConversation, isPending } = useCreateConversation();
  const { providers } = useUserProviders();
  const { connect, reconnect } = useSubscribeToConversation();

  const createConversationAndSubscribe = React.useCallback(
    ({
      query,
      conversationInstructions,
      repository,
      onSuccessCallback,
    }: {
      query: string;
      conversationInstructions: string;
      repository: {
        name: string;
        branch: string;
        gitProvider: Provider;
      };
      onSuccessCallback?: () => void;
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

            const opts: UseSubscribeToConversationOptions = {
              conversation_id: data.conversation_id,
              session_api_key: data.session_api_key,
              providers_set: providers,
            };

            const handleOhEvent = (event: unknown) => {
              console.warn(event);

              if (isErrorEvent(event) || isAgentStatusError(event)) {
                renderConversationErroredToast(event.message, () => {
                  reconnect(baseUrl, opts, { oh_event: handleOhEvent });
                });
              } else if (isStatusUpdate(event)) {
                if (
                  event.type === "info" &&
                  event.id === "STATUS$STARTING_RUNTIME"
                ) {
                  renderConversationCreatedToast(data.conversation_id);
                }
              } else if (
                isOpenHandsEvent(event) &&
                isAgentStateChangeObservation(event)
              ) {
                if (event.extras.agent_state === AgentState.FINISHED) {
                  renderConversationFinishedToast(data.conversation_id);
                }
              }
            };

            connect(baseUrl, opts, { oh_event: handleOhEvent });
            onSuccessCallback?.();
          },
        },
      );
    },
    [createConversation, connect, reconnect, providers],
  );

  return { createConversationAndSubscribe, isPending };
};
