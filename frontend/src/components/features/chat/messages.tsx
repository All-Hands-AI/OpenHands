import React from "react";
import type { Message } from "#/message";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { getCriticScoreColor, ExpandableMessage } from "./expandable-message";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";
import { useProgressModal } from "#/hooks/use-progress-modal";

interface MessagesProps {
  messages: Message[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) => {
    const { conversationId } = useConversation();
    const { data: conversation } = useUserConversation(conversationId || null);
    const { openProgressModal } = useProgressModal();

    // Function to handle click on critic score
    const handleCriticScoreClick = (criticScore?: number) => {
      if (criticScore !== undefined && conversationId) {
        openProgressModal(conversationId);
      }
    };

    // Check if conversation metadata has trigger=resolver
    const isResolverTrigger = conversation?.trigger === "resolver";

    return messages.map((message, index) => {
      const shouldShowConfirmationButtons =
        messages.length - 1 === index &&
        message.sender === "assistant" &&
        isAwaitingUserConfirmation;

      const isFirstUserMessageWithResolverTrigger =
        index === 0 && message.sender === "user" && isResolverTrigger;

      // Special case: First user message with resolver trigger
      if (isFirstUserMessageWithResolverTrigger) {
        return (
          <div key={index}>
            <ExpandableMessage
              type="action"
              message={message.content}
              id={I18nKey.CHAT$RESOLVER_INSTRUCTIONS}
            />
            {message.imageUrls && message.imageUrls.length > 0 && (
              <ImageCarousel size="small" images={message.imageUrls} />
            )}
          </div>
        );
      }

      if (message.type === "error" || message.type === "action") {
        return (
          <div key={index}>
            <ExpandableMessage
              type={message.type}
              id={message.translationID}
              message={message.content}
              success={message.success}
              observation={message.observation}
              action={message.action}
              criticScore={message.criticScore}
            />
            {shouldShowConfirmationButtons && <ConfirmationButtons />}
          </div>
        );
      }

      // Handle messages with critic scores - use ChatMessage with border color
      if (message.criticScore !== undefined && message.criticScore !== 0) {
        const borderColorClass = getCriticScoreColor(message.criticScore);
        return (
          <div
            key={index}
            className={`border-l-4 ${borderColorClass} pl-2 py-2 my-2 cursor-pointer hover:border-l-6 transition-all duration-200`}
            onClick={() => handleCriticScoreClick(message.criticScore)}
          >
            <ChatMessage type={message.sender} message={message.content}>
              {message.imageUrls && message.imageUrls.length > 0 && (
                <ImageCarousel size="small" images={message.imageUrls} />
              )}
              {shouldShowConfirmationButtons && <ConfirmationButtons />}
            </ChatMessage>
          </div>
        );
      }

      return (
        <ChatMessage
          key={index}
          type={message.sender}
          message={message.content}
        >
          {message.imageUrls && message.imageUrls.length > 0 && (
            <ImageCarousel size="small" images={message.imageUrls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
      );
    });
  },
);

Messages.displayName = "Messages";
