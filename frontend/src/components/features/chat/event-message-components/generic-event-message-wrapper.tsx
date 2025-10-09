import { ChatMessage } from "../chat-message";
import { GenericEventMessage } from "../generic-event-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";
import { OpenHandsEvent } from "#/types/v1/core";
import { isActionEvent, isObservationEvent } from "#/types/v1/type-guards";

interface GenericEventMessageWrapperProps {
  event: OpenHandsEvent;
  shouldShowConfirmationButtons: boolean;
}

export function GenericEventMessageWrapper({
  event,
  shouldShowConfirmationButtons,
}: GenericEventMessageWrapperProps) {
  return (
    <div>
      {isActionEvent(event) && event.action.kind !== "ThinkAction" && (
        <ChatMessage type="agent" message={event.thought[0].text} />
      )}

      <GenericEventMessage
        title={getEventContent(event).title}
        details={getEventContent(event).details}
        success={
          isObservationEvent(event) ? getObservationResult(event) : undefined
        }
      />

      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
