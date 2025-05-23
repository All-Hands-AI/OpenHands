import React from "react";
import { FaCircleUp } from "react-icons/fa6";
import { createPortal } from "react-dom";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsEventType } from "#/types/core/base";
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
import { useConversation } from "#/context/conversation-context";

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

const COMMON_NO_RENDER_LIST: OpenHandsEventType[] = [
  "system",
  "agent_state_changed",
  "change_agent_state",
];

const ACTION_NO_RENDER_LIST: OpenHandsEventType[] = ["recall"];

const shouldRenderEvent = (event: OpenHandsAction | OpenHandsObservation) => {
  if (isOpenHandsAction(event)) {
    const noRenderList = COMMON_NO_RENDER_LIST.concat(ACTION_NO_RENDER_LIST);
    return !noRenderList.includes(event.action);
  }

  if (isOpenHandsObservation(event)) {
    return !COMMON_NO_RENDER_LIST.includes(event.observation);
  }

  return true;
};

interface MessagesProps {
  messages: (OpenHandsAction | OpenHandsObservation)[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { getOptimisticUserMessage } = useOptimisticUserMessage();
    const { providers } = useUserProviders();
    const { mutate: createConversation } = useCreateConversation();
    const { conversationId } = useConversation();
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
      description: string,
      target: string,
      triggers: string[],
    ) => {
      const query = `Target file: ${target}\n\nDescription: ${description}\n\nTriggers: ${triggers.join(", ")}`;

      createConversation(
        { q: query },
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
        {messages.filter(shouldRenderEvent).map((message, index) => (
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
);

Messages.displayName = "Messages";
