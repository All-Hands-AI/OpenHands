import React from "react";
import { OpenHandsEvent } from "#/types/v1/core";
import { GenericEventMessage } from "../../../features/chat/generic-event-message";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";
import { isObservationEvent } from "#/types/v1/type-guards";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";

interface GenericEventMessageWrapperProps {
  event: OpenHandsEvent;
  shouldShowConfirmationButtons: boolean;
}

export function GenericEventMessageWrapper({
  event,
  shouldShowConfirmationButtons,
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
      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
