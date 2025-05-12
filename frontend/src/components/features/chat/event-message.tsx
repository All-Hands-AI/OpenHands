import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { I18nKey } from "#/i18n/declaration";
import { OpenHandsAction } from "#/types/core/actions";
import {
  isUserMessage,
  isErrorObservation,
  isAssistantMessage,
  isCommandObservation,
} from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { ImageCarousel } from "../images/image-carousel";
import { ChatMessage } from "./chat-message";
import { ErrorMessage } from "./error-message";
import { getEventContent, isSuccessObservation } from "./event-message.helpers";
import { ExpandableMessage } from "./expandable-message";
import { GenericEventMessage } from "./generic-event-message";

interface EventMessageProps {
  event: OpenHandsAction | OpenHandsObservation;
  isFirstMessageWithResolverTrigger: boolean;
  isAwaitingUserConfirmation: boolean;
  isLastMessage: boolean;
}

export function EventMessage({
  event,
  isFirstMessageWithResolverTrigger,
  isAwaitingUserConfirmation,
  isLastMessage,
}: EventMessageProps) {
  const shouldShowConfirmationButtons =
    isLastMessage && event.source === "agent" && isAwaitingUserConfirmation;

  const isFirstUserMessageWithResolverTrigger =
    isFirstMessageWithResolverTrigger && isUserMessage(event);

  // Special case: First user message with resolver trigger
  if (isFirstUserMessageWithResolverTrigger) {
    return (
      <div>
        <ExpandableMessage
          type="action"
          message={event.args.content}
          id={I18nKey.CHAT$RESOLVER_INSTRUCTIONS}
        />
        {event.args.image_urls && event.args.image_urls.length > 0 && (
          <ImageCarousel size="small" images={event.args.image_urls} />
        )}
      </div>
    );
  }

  if (isErrorObservation(event)) {
    return (
      <ErrorMessage
        errorId={event.extras.error_id}
        defaultMessage={event.message}
      />
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    return (
      <ChatMessage
        type={event.source}
        message={isUserMessage(event) ? event.args.content : event.message}
      >
        {event.args.image_urls && event.args.image_urls.length > 0 && (
          <ImageCarousel size="small" images={event.args.image_urls} />
        )}
        {shouldShowConfirmationButtons && <ConfirmationButtons />}
      </ChatMessage>
    );
  }

  return (
    <div>
      <GenericEventMessage
        title={getEventContent(event).title}
        details={getEventContent(event).details}
        success={
          isCommandObservation(event) ? isSuccessObservation(event) : undefined
        }
      />

      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
