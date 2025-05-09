import React from "react";
import { Trans } from "react-i18next";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { ExpandableMessage } from "./expandable-message";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import {
  isAssistantMessage,
  isCommandObservation,
  isErrorObservation,
  isOpenHandsAction,
  isOpenHandsObservation,
  isUserMessage,
} from "#/types/core/guards";
import { ErrorMessage } from "./error-message";
import { MonoComponent } from "./mono-component";
import { GenericEventMessage } from "./generic-event-message";

const trimText = (text: string, maxLength: number): string => {
  if (!text) return "";
  return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

const getActionContent = (action: OpenHandsAction) => {
  const content: { title: React.ReactNode; details: string } = {
    title: "",
    details: "",
  };

  switch (action.action) {
    case "run":
      content.title = (
        <Trans
          i18nKey="ACTION_MESSAGE$RUN"
          values={{
            command: trimText(action.args.command, 80),
          }}
          components={{
            cmd: <MonoComponent />,
          }}
        />
      );
      content.details = `Command:\n\`${action.args.command}\``;
      break;
    default:
      content.title = action.action;
      content.details = JSON.stringify(action.args, null, 2);
      break;
  }

  return content;
};

const getObservationContent = (observation: OpenHandsObservation) => {
  const content: { title: React.ReactNode; details: string } = {
    title: "",
    details: "",
  };

  switch (observation.observation) {
    case "run":
      content.title = (
        <Trans
          i18nKey="OBSERVATION_MESSAGE$RUN"
          values={{
            command: trimText(observation.extras.command, 80),
          }}
          components={{
            cmd: <MonoComponent />,
          }}
        />
      );

      content.details = `Command:\n\`${observation.extras.command}\`\n\nOutput:\n\`\`\`\n${observation.content || "[Command finished execution with no output]"}\n\`\`\``;
      break;
    default:
      content.title = observation.observation;
      content.details = JSON.stringify(observation.extras, null, 2);
      break;
  }

  return content;
};

const getContent = (event: OpenHandsAction | OpenHandsObservation) => {
  if (isOpenHandsAction(event)) {
    return getActionContent(event);
  }
  if (isOpenHandsObservation(event)) {
    return getObservationContent(event);
  }
  return { title: "Unknown event", details: "Unknown event" };
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

    return messages.map((message, index) => {
      const shouldShowConfirmationButtons =
        messages.length - 1 === index &&
        message.source === "agent" &&
        isAwaitingUserConfirmation;

      const isFirstUserMessageWithResolverTrigger =
        isUserMessage(message) && index === 0 && isResolverTrigger;

      // Special case: First user message with resolver trigger
      if (isFirstUserMessageWithResolverTrigger) {
        return (
          <div key={index}>
            <ExpandableMessage
              type="action"
              message={message.args.content}
              id={I18nKey.CHAT$RESOLVER_INSTRUCTIONS}
            />
            {message.args.image_urls && message.args.image_urls.length > 0 && (
              <ImageCarousel size="small" images={message.args.image_urls} />
            )}
          </div>
        );
      }

      if (isErrorObservation(message)) {
        return (
          <ErrorMessage
            key={index}
            errorId={message.extras.error_id}
            defaultMessage={message.message}
          />
        );
      }

      if (isUserMessage(message) || isAssistantMessage(message)) {
        return (
          <ChatMessage
            key={index}
            type={message.source}
            message={
              isUserMessage(message) ? message.args.content : message.message
            }
          >
            {message.args.image_urls && message.args.image_urls.length > 0 && (
              <ImageCarousel size="small" images={message.args.image_urls} />
            )}
            {shouldShowConfirmationButtons && <ConfirmationButtons />}
          </ChatMessage>
        );
      }

      return (
        <div key={index}>
          <GenericEventMessage
            title={getContent(message).title}
            details={getContent(message).details}
            success={
              isCommandObservation(message)
                ? message.extras.metadata.exit_code === 0
                : undefined
            }
          />

          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </div>
      );
    });
  },
);

Messages.displayName = "Messages";
