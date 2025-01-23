import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { ExpandableMessage } from "./expandable-message";

interface MessagesProps {
  messages: Message[];
  isAwaitingUserConfirmation: boolean;
}

export function Messages({
  messages,
  isAwaitingUserConfirmation,
}: MessagesProps) {
  return messages.map((message, index) => {
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
          />
          {shouldShowConfirmationButtons && <ConfirmationButtons />}
        </div>
      );
    }

    return (
      <ChatMessage key={index} type={message.sender} message={message.content}>
        {message.imageUrls && message.imageUrls.length > 0 && (
          <ImageCarousel size="small" images={message.imageUrls} />
        )}
        {shouldShowConfirmationButtons && <ConfirmationButtons />}
      </ChatMessage>
    );
  });
}
