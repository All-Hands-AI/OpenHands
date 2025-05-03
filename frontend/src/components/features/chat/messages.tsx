import React from "react";
import type { Message } from "#/message";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { ExpandableMessage } from "./expandable-message";

interface MessagesProps {
  messages: Message[];
  isAwaitingUserConfirmation: boolean;
}

export const Messages: React.FC<MessagesProps> = React.memo(
  ({ messages, isAwaitingUserConfirmation }) =>
    messages.map((message, index) => {
      const shouldShowConfirmationButtons =
        messages.length - 1 === index &&
        message.sender === "assistant" &&
        isAwaitingUserConfirmation;

      if (message.type === "error" || message.type === "action") {
        return (
          <div key={index}>
            <ExpandableMessage
              type={message.type}
              id={message.translationID}
              message={message.content}
              success={message.success}
              eventID={message.eventID} // add id
            />
            {shouldShowConfirmationButtons && <ConfirmationButtons />}
          </div>
        );
      }

      return (
        <ChatMessage
          key={index}
          type={message.sender}
          message={message.content}
          id={message.eventID} // add id
        >
          {message.imageUrls && message.imageUrls.length > 0 && (
            <ImageCarousel size="small" images={message.imageUrls} />
          )}
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </ChatMessage>
      );
    }),
);

Messages.displayName = "Messages";
