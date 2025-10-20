import React from "react";
import { OpenHandsEvent } from "#/types/v1/core";
import { isActionEvent, isObservationEvent } from "#/types/v1/type-guards";
import { EventMessage } from "./event-message";
import { ChatMessage } from "../../features/chat/chat-message";
import { useOptimisticUserMessageStore } from "#/stores/optimistic-user-message-store";
// TODO: Implement microagent functionality for V1 when APIs support V1 event IDs
// import { AgentState } from "#/types/agent-state";
// import MemoryIcon from "#/icons/memory_icon.svg?react";

interface MessagesProps {
  messages: OpenHandsEvent[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { getOptimisticUserMessage } = useOptimisticUserMessageStore();

    const optimisticUserMessage = getOptimisticUserMessage();

    const actionHasObservationPair = React.useCallback(
      (event: OpenHandsEvent): boolean => {
        if (isActionEvent(event)) {
          // Check if there's a corresponding observation event
          return !!messages.some(
            (msg) => isObservationEvent(msg) && msg.action_id === event.id,
          );
        }

        return false;
      },
      [messages],
    );

    // TODO: Implement microagent functionality for V1 if needed
    // For now, we'll skip microagent features

    return (
      <>
        {messages.map((message, index) => (
          <EventMessage
            key={message.id}
            event={message}
            hasObservationPair={actionHasObservationPair(message)}
            isAwaitingUserConfirmation={isAwaitingUserConfirmation}
            isLastMessage={messages.length - 1 === index}
            isInLast10Actions={messages.length - 1 - index < 10}
            // Microagent props - not implemented yet for V1
            // microagentStatus={undefined}
            // microagentConversationId={undefined}
            // microagentPRUrl={undefined}
            // actions={undefined}
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
