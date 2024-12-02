import { ChatMessage } from "#/components/features/chat/chat-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { ImageCarousel } from "../images/image-carousel";
import { ErrorMessage } from "./error-message";

const isErrorMessage = (
  message: Message | ErrorMessage,
): message is ErrorMessage => "error" in message;

interface MessagesProps {
  messages: (Message | ErrorMessage)[];
  isAwaitingUserConfirmation: boolean;
}

export function Messages({
  messages,
  isAwaitingUserConfirmation,
}: MessagesProps) {
  return messages.map((message, index) =>
    isErrorMessage(message) ? (
      <ErrorMessage key={index} id={message.id} message={message.message} />
    ) : (
      <ChatMessage key={index} type={message.sender} message={message.content}>
        {message.imageUrls.length > 0 && (
          <ImageCarousel size="small" images={message.imageUrls} />
        )}
        {messages.length - 1 === index &&
          message.sender === "assistant" &&
          isAwaitingUserConfirmation && <ConfirmationButtons />}
      </ChatMessage>
    ),
  );
}
