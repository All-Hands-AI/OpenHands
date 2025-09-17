import React from "react";
import { OpenHandsObservation } from "#/types/core/observations";
import { isMcpObservation } from "#/types/core/guards";
import { GenericEventMessage } from "../generic-event-message";
import { MCPObservationContent } from "../mcp-observation-content";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";

interface McpEventMessageProps {
  event: OpenHandsObservation;
  shouldShowConfirmationButtons: boolean;
}

export function McpEventMessage({
  event,
  shouldShowConfirmationButtons,
}: McpEventMessageProps) {
  if (!isMcpObservation(event)) {
    return null;
  }

  return (
    <div>
      <GenericEventMessage
        title={getEventContent(event).title}
        details={<MCPObservationContent event={event} />}
        success={getObservationResult(event)}
      />
      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
