import React from "react";
import { FaCircleUp } from "react-icons/fa6";
import { createPortal } from "react-dom";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { EventMessage } from "./event-message";
import { ChatMessage } from "./chat-message";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { LaunchMicroagentModal } from "./launch-miocroagent-modal";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import {
  useSubscribeToConversation,
  UseSubscribeToConversationOptions,
} from "#/hooks/use-subscribe-to-conversation";
import { useUserProviders } from "#/hooks/use-user-providers";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversationId } from "#/hooks/use-conversation-id";

interface LaunchToMicroagentButtonProps {
  onClick: () => void;
}

function LaunchToMicroagentButton({ onClick }: LaunchToMicroagentButtonProps) {
  return (
    <button
      data-testid="launch-microagent-button"
      type="button"
      onClick={onClick}
      className="w-7 h-7 border border-white/30 bg-white/20 rounded flex items-center justify-center"
    >
      <FaCircleUp className="w-[14px] h-[14px]" />
    </button>
  );
}

interface MessagesProps {
  messages: (OpenHandsAction | OpenHandsObservation)[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { getOptimisticUserMessage } = useOptimisticUserMessage();
    const { providers } = useUserProviders();
    const { mutate: createConversation } = useCreateConversation();
    const { conversationId } = useConversationId();
    const { data: conversation } = useUserConversation(conversationId);

    const { connect } = useSubscribeToConversation();
    const optimisticUserMessage = getOptimisticUserMessage();

    const [selectedEventId, setSelectedEventId] = React.useState<number | null>(
      null,
    );
    const [showLaunchMicroagentModal, setShowLaunchMicroagentModal] =
      React.useState(false);

    const actionHasObservationPair = React.useCallback(
      (event: OpenHandsAction | OpenHandsObservation): boolean => {
        if (isOpenHandsAction(event)) {
          return !!messages.some(
            (msg) => isOpenHandsObservation(msg) && msg.cause === event.id,
          );
        }

        return false;
      },
      [messages],
    );

    const handleLaunchMicroagent = (
      query: string,
      target: string,
      triggers: string[],
    ) => {
      const conversationInstructions = `Target file: ${target}\n\nDescription: ${query}\n\nTriggers: ${triggers.join(", ")}`;
      if (
        !conversation ||
        !conversation.selected_repository ||
        !conversation.selected_branch ||
        !conversation.git_provider
      ) {
        console.warn("No repository found to launch microagent");
        return;
      }

      createConversation(
        {
          query,
          conversationInstructions,
          repository: {
            name: conversation.selected_repository,
            branch: conversation.selected_branch,
            gitProvider: conversation.git_provider,
          },
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
            connect({
              url: baseUrl,
              query: opts,
            });
          },
        },
      );
    };

    return (
      <>
        {messages.map((message, index) => (
          <EventMessage
            key={index}
            event={message}
            hasObservationPair={actionHasObservationPair(message)}
            isAwaitingUserConfirmation={isAwaitingUserConfirmation}
            isLastMessage={messages.length - 1 === index}
            assistantMessageActionButton={
              <LaunchToMicroagentButton
                onClick={() => {
                  setSelectedEventId(message.id);
                  setShowLaunchMicroagentModal(true);
                }}
              />
            }
          />
        ))}

        {optimisticUserMessage && (
          <ChatMessage type="user" message={optimisticUserMessage} />
        )}
        {showLaunchMicroagentModal &&
          selectedEventId &&
          createPortal(
            <LaunchMicroagentModal
              onClose={() => setShowLaunchMicroagentModal(false)}
              onLaunch={handleLaunchMicroagent}
              eventId={selectedEventId}
              selectedRepo={conversation?.selected_repository?.split("/").pop()}
            />,
            document.getElementById("modal-portal-exit") || document.body,
          )}
      </>
    );
  },
  (prevProps, nextProps) => {
    // Prevent re-renders if messages are the same length
    if (prevProps.messages.length !== nextProps.messages.length) {
      return false;
    }

    return true;
  },
);

Messages.displayName = "Messages";
