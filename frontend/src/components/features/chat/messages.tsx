import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { ErrorMessage } from "./error-message";
import { ExpandableMessage } from "./expandable-message";

interface ErrorMessageType {
  type: "error";
  id: string;
  message: string;
}

const isErrorMessage = (
  message: Message | ErrorMessageType,
): message is ErrorMessageType => "error" in message;

interface MessagesProps {
  messages: (Message | ErrorMessageType)[];
  isAwaitingUserConfirmation: boolean;
}

export function Messages({
  messages,
  isAwaitingUserConfirmation,
}: MessagesProps) {
  return messages.map((message, index) => {
    if (isErrorMessage(message)) {
      return <ErrorMessage key={index} message={message.message} />;
    }

    if (message.type === "action") {
      return (
        <ExpandableMessage
          key={index}
          type={message.type}
          id={message.id}
          message={message.content}
        />
      );
    }

    return (
      <ChatMessage key={index} type={message.sender} message={message.content}>
        {message.imageUrls && message.imageUrls.length > 0 && (
          <ImageCarousel size="small" images={message.imageUrls} />
        )}
        {messages.length - 1 === index &&
          message.sender === "assistant" &&
          isAwaitingUserConfirmation && <ConfirmationButtons />}
      </ChatMessage>
    );
  });
}
