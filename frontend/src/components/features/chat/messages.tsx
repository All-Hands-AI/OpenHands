import React from "react";
import { createPortal } from "react-dom";
import { FaBrain } from "react-icons/fa6";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import {
  isOpenHandsAction,
  isOpenHandsObservation,
  isOpenHandsEvent,
  isAgentStateChangeObservation,
} from "#/types/core/guards";
import { EventMessage } from "./event-message";
import { ChatMessage } from "./chat-message";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { LaunchMicroagentModal } from "./microagent/launch-microagent-modal";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useCreateConversationAndSubscribeMultiple } from "#/hooks/use-create-conversation-and-subscribe-multiple";
import {
  MicroagentStatus,
  EventMicroagentStatus,
} from "#/types/microagent-status";
import { AgentState } from "#/types/agent-state";

interface MessagesProps {
  messages: (OpenHandsAction | OpenHandsObservation)[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { createConversationAndSubscribe, isPending } =
      useCreateConversationAndSubscribeMultiple();
    const { getOptimisticUserMessage } = useOptimisticUserMessage();
    const { conversationId } = useConversationId();
    const { data: conversation } = useUserConversation(conversationId);

    const optimisticUserMessage = getOptimisticUserMessage();

    const [selectedEventId, setSelectedEventId] = React.useState<number | null>(
      null,
    );
    const [showLaunchMicroagentModal, setShowLaunchMicroagentModal] =
      React.useState(false);
    const [microagentStatuses, setMicroagentStatuses] = React.useState<
      EventMicroagentStatus[]
    >([]);

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

    const getMicroagentStatusForEvent = React.useCallback(
      (eventId: number): MicroagentStatus | null => {
        const statusEntry = microagentStatuses.find(
          (entry) => entry.eventId === eventId,
        );
        return statusEntry?.status || null;
      },
      [microagentStatuses],
    );

    const handleMicroagentEvent = React.useCallback(
      (socketEvent: unknown, microagentConversationId: string) => {
        // Handle error events
        const isErrorEvent = (
          evt: unknown,
        ): evt is { error: true; message: string } =>
          typeof evt === "object" &&
          evt !== null &&
          "error" in evt &&
          evt.error === true;

        const isAgentStatusError = (evt: unknown): boolean =>
          isOpenHandsEvent(evt) &&
          isAgentStateChangeObservation(evt) &&
          evt.extras.agent_state === AgentState.ERROR;

        if (isErrorEvent(socketEvent) || isAgentStatusError(socketEvent)) {
          setMicroagentStatuses((prev) =>
            prev.map((statusEntry) =>
              statusEntry.conversationId === microagentConversationId
                ? { ...statusEntry, status: MicroagentStatus.ERROR }
                : statusEntry,
            ),
          );
        } else if (
          isOpenHandsEvent(socketEvent) &&
          isAgentStateChangeObservation(socketEvent)
        ) {
          if (socketEvent.extras.agent_state === AgentState.FINISHED) {
            setMicroagentStatuses((prev) =>
              prev.map((statusEntry) =>
                statusEntry.conversationId === microagentConversationId
                  ? { ...statusEntry, status: MicroagentStatus.COMPLETED }
                  : statusEntry,
              ),
            );
          }
        }
      },
      [setMicroagentStatuses],
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
        !conversation.git_provider ||
        !selectedEventId
      ) {
        return;
      }

      // Set initial status to creating
      setMicroagentStatuses((prev) => [
        ...prev.filter((status) => status.eventId !== selectedEventId),
        {
          eventId: selectedEventId,
          conversationId: "", // Will be updated when conversation is created
          status: MicroagentStatus.CREATING,
        },
      ]);

      createConversationAndSubscribe({
        query,
        conversationInstructions,
        repository: {
          name: conversation.selected_repository,
          branch: conversation.selected_branch,
          gitProvider: conversation.git_provider,
        },
        onSuccessCallback: (newConversationId: string) => {
          setShowLaunchMicroagentModal(false);
          // Update status with conversation ID
          setMicroagentStatuses((prev) =>
            prev.map((statusEntry) =>
              statusEntry.eventId === selectedEventId
                ? {
                    ...statusEntry,
                    conversationId: newConversationId,
                    status: MicroagentStatus.CREATING,
                  }
                : statusEntry,
            ),
          );
        },
        onEventCallback: (socketEvent: unknown, newConversationId: string) => {
          handleMicroagentEvent(socketEvent, newConversationId);
        },
      });
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
            microagentStatus={getMicroagentStatusForEvent(message.id)}
            actions={[
              {
                icon: <FaBrain className="w-[14px] h-[14px]" />,
                onClick: () => {
                  setSelectedEventId(message.id);
                  setShowLaunchMicroagentModal(true);
                },
              },
            ]}
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
              isLoading={isPending}
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
