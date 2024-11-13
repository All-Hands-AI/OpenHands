import { UserMessageAction } from "#/types/core/actions";
import { LocalUserMessageAction } from "#/types/core/variances";
import {
  isLocalUserMessage,
  isUserMessageAction,
  isAssistantMessageAction,
} from "#/utils/type-guards";
import { ChatMessage } from "./chat-message";
import ConfirmationButtons from "./chat/ConfirmationButtons";
import { ErrorMessage } from "./error-message";
import { ImageCarousel } from "./image-carousel";

const isErrorMessage = (
  message: Record<string, unknown>,
): message is ErrorMessage => "error" in message;

const isUserMessage = (
  message: unknown,
): message is LocalUserMessageAction | UserMessageAction =>
  isLocalUserMessage(message) || isUserMessageAction(message);

interface EventMessageProps {
  message: Record<string, unknown>;
  isAwaitingUserConfirmation?: boolean;
}

export function EventMessage({
  message,
  isAwaitingUserConfirmation,
}: EventMessageProps) {
  if (isErrorMessage(message)) {
    return <ErrorMessage id={message.id} message={message.message} />;
  }

  if (isAssistantMessageAction(message)) {
    return (
      <ChatMessage type="assistant" message={message.args.content}>
        {isAwaitingUserConfirmation && <ConfirmationButtons />}
      </ChatMessage>
    );
  }

  if (isUserMessage(message)) {
    return (
      <ChatMessage type="user" message={message.args.content}>
        {message.args.image_urls.length > 0 && (
          <ImageCarousel size="small" images={message.args.image_urls} />
        )}
      </ChatMessage>
    );
  }

  return null;
}
