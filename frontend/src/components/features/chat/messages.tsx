import React from "react";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversation } from "#/context/conversation-context";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsEventType } from "#/types/core/base";
import { EventMessage } from "./event-message";

const NO_RENDER_LIST: OpenHandsEventType[] = [
  "system",
  "recall",
  "agent_state_changed",
  "change_agent_state",
];

const shouldRenderEvent = (event: OpenHandsAction | OpenHandsObservation) => {
  let eventType: OpenHandsEventType | null = null;

  if (isOpenHandsAction(event)) {
    eventType = event.action;
  }
  if (isOpenHandsObservation(event)) {
    eventType = event.observation;
  }

  return eventType ? !NO_RENDER_LIST.includes(eventType) : false;
};

interface MessagesProps {
  messages: (OpenHandsAction | OpenHandsObservation)[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { conversationId } = useConversation();
    const { data: conversation } = useUserConversation(conversationId || null);

    // Check if conversation metadata has trigger=resolver
    const isResolverTrigger = conversation?.trigger === "resolver";

    return messages
      .filter(shouldRenderEvent)
      .map((message, index) => (
        <EventMessage
          key={index}
          event={message}
          isFirstMessageWithResolverTrigger={index === 0 && isResolverTrigger}
          isAwaitingUserConfirmation={isAwaitingUserConfirmation}
          isLastMessage={messages.length - 1 === index}
        />
      ));
  },
);

Messages.displayName = "Messages";
