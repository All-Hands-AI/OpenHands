import { ChatMessage } from "#/components/chat-message";
import ConfirmationButtons from "#/components/chat/confirmation-buttons";
import { ErrorMessage } from "#/components/error-message";
import { ImageCarousel } from "#/components/image-carousel";

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
