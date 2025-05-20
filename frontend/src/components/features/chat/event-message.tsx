import { FaCircleUp } from "react-icons/fa6";
import { createPortal } from "react-dom";
import React from "react";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { I18nKey } from "#/i18n/declaration";
import { OpenHandsAction } from "#/types/core/actions";
import {
  isUserMessage,
  isErrorObservation,
  isAssistantMessage,
  isOpenHandsAction,
  isOpenHandsObservation,
  isFinishAction,
  isRejectObservation,
} from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { ImageCarousel } from "../images/image-carousel";
import { ChatMessage } from "./chat-message";
import { ErrorMessage } from "./error-message";
import { getObservationResult } from "./event-content-helpers/get-observation-result";
import { getEventContent } from "./event-content-helpers/get-event-content";
import { ExpandableMessage } from "./expandable-message";
import { GenericEventMessage } from "./generic-event-message";
import { LaunchMicroagentModal } from "./launch-miocroagent-modal";

interface LaunchToMicroagentButtonProps {
  onClick: () => void;
}

function LaunchToMicroagentButton({ onClick }: LaunchToMicroagentButtonProps) {
  return (
    <button
      data-testid="launch-microagent-button"
      type="button"
      onClick={onClick}
      className="w-7 h-7 border border-white/30 bg-white/20 rounded flex items-center justify-center"
    >
      <FaCircleUp className="w-[14px] h-[14px]" />
    </button>
  );
}

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

interface EventMessageProps {
  event: OpenHandsAction | OpenHandsObservation;
  hasObservationPair: boolean;
  isFirstMessageWithResolverTrigger: boolean;
  isAwaitingUserConfirmation: boolean;
  isLastMessage: boolean;
}

export function EventMessage({
  event,
  hasObservationPair,
  isFirstMessageWithResolverTrigger,
  isAwaitingUserConfirmation,
  isLastMessage,
}: EventMessageProps) {
  const [showLaunchMicroagentModal, setShowLaunchMicroagentModal] =
    React.useState(false);

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

  const handleLaunchMicroagent = () => {
    setShowLaunchMicroagentModal(true);
  };

  if (isErrorObservation(event)) {
    return (
      <ErrorMessage
        errorId={event.extras.error_id}
        defaultMessage={event.message}
      />
    );
  }

  if (
    hasObservationPair &&
    isOpenHandsAction(event) &&
    hasThoughtProperty(event.args)
  ) {
    return <ChatMessage type="agent" message={event.args.thought} />;
  }

  if (isFinishAction(event)) {
    return (
      <ChatMessage type="agent" message={getEventContent(event).details} />
    );
  }

  if (isUserMessage(event) || isAssistantMessage(event)) {
    return (
      <ChatMessage
        type={event.source}
        message={isUserMessage(event) ? event.args.content : event.message}
        actionButton={
          <LaunchToMicroagentButton onClick={handleLaunchMicroagent} />
        }
      >
        {event.args.image_urls && event.args.image_urls.length > 0 && (
          <ImageCarousel size="small" images={event.args.image_urls} />
        )}
        {shouldShowConfirmationButtons && <ConfirmationButtons />}
        {showLaunchMicroagentModal &&
          createPortal(
            <LaunchMicroagentModal
              onClose={() => setShowLaunchMicroagentModal(false)}
            />,
            document.getElementById("modal-portal-exit") || document.body,
          )}
      </ChatMessage>
    );
  }

  if (isRejectObservation(event)) {
    return <ChatMessage type="agent" message={event.content} />;
  }

  return (
    <div>
      {isOpenHandsAction(event) && hasThoughtProperty(event.args) && (
        <ChatMessage type="agent" message={event.args.thought} />
      )}

      <GenericEventMessage
        title={getEventContent(event).title}
        details={getEventContent(event).details}
        success={
          isOpenHandsObservation(event)
            ? getObservationResult(event)
            : undefined
        }
      />

      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
