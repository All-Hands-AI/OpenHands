import React from "react";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { EventMessage } from "./event-message";
import { ChatMessage } from "./chat-message";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";

interface MessagesProps {
  messages: (OpenHandsAction | OpenHandsObservation)[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { getOptimisticUserMessage } = useOptimisticUserMessage();

    const optimisticUserMessage = getOptimisticUserMessage();

    const actionHasObservationPair = React.useCallback(
      (event: OpenHandsAction | OpenHandsObservation): boolean => {
        if (isOpenHandsAction(event)) {
          return !!messages.some(
            (msg) => isOpenHandsObservation(msg) && msg.cause === event.id,
          );
        }

        return false;
      },
      [],
    );

    return (
      <>
        {messages.map((message, index) => (
          <EventMessage
            key={index}
            event={message}
            hasObservationPair={actionHasObservationPair(message)}
            isAwaitingUserConfirmation={isAwaitingUserConfirmation}
            isLastMessage={messages.length - 1 === index}
          />
        ))}

        {optimisticUserMessage && (
          <ChatMessage type="user" message={optimisticUserMessage} />
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
