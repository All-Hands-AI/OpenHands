import { OpenHandsEvent } from "#/types/v1/core";
import { GenericEventMessage } from "../../../features/chat/generic-event-message";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";
import { isObservationEvent } from "#/types/v1/type-guards";
import { V1ConfirmationButtons } from "#/components/shared/buttons/v1-confirmation-buttons";

interface GenericEventMessageWrapperProps {
  event: OpenHandsEvent;
  isLastMessage: boolean;
}

export function GenericEventMessageWrapper({
  event,
  isLastMessage,
}: GenericEventMessageWrapperProps) {
  const { title, details } = getEventContent(event);

  return (
    <div>
      <GenericEventMessage
        title={title}
        details={details}
        success={
          isObservationEvent(event) ? getObservationResult(event) : undefined
        }
        initiallyExpanded={false}
      />
      {isLastMessage && <V1ConfirmationButtons />}
    </div>
  );
}
