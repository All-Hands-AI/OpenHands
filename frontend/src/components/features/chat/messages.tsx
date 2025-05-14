import React from "react";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversation } from "#/context/conversation-context";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsEventType } from "#/types/core/base";
import { EventMessage } from "./event-message";
import { ChatMessage } from "./chat-message";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { useWSErrorMessage } from "#/hooks/use-ws-error-message";
import { ErrorMessage } from "./error-message";

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

/*
// Used to check if an action has a corresponding observation
// Useful for filtering out actions that have an observation (result)

const actionHasObservationPair = (
  event: OpenHandsAction | OpenHandsObservation,
  messages: (OpenHandsAction | OpenHandsObservation)[],
): boolean => {
  if (isOpenHandsAction(event)) {
    return !messages.some(
      (msg) => isOpenHandsObservation(msg) && msg.cause === event.id,
    );
  }

  return true;
};
*/

interface MessagesProps {
  messages: (OpenHandsAction | OpenHandsObservation)[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { getOptimisticUserMessage } = useOptimisticUserMessage();
    const { getErrorMessage } = useWSErrorMessage();
    const { conversationId } = useConversation();
    const { data: conversation } = useUserConversation(conversationId || null);

    const optimisticUserMessage = getOptimisticUserMessage();
    const errorMessage = getErrorMessage();

    // Check if conversation metadata has trigger=resolver
    const isResolverTrigger = conversation?.trigger === "resolver";

    return (
      <>
        {messages.filter(shouldRenderEvent).map((message, index) => (
          <EventMessage
            key={index}
            event={message}
            isFirstMessageWithResolverTrigger={index === 0 && isResolverTrigger}
            isAwaitingUserConfirmation={isAwaitingUserConfirmation}
            isLastMessage={messages.length - 1 === index}
          />
        ))}

        {optimisticUserMessage && (
          <ChatMessage type="user" message={optimisticUserMessage} />
        )}

        {errorMessage && <ErrorMessage defaultMessage={errorMessage} />}
      </>
    );
  },
);

Messages.displayName = "Messages";
