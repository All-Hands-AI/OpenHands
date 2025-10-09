import React from "react";
import { GenericEventMessage } from "../generic-event-message";
import { MCPObservationContent } from "../mcp-observation-content";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";

interface McpEventMessageProps {
  event: {
    message: string;
    arguments: Record<string, unknown>;
  };
  shouldShowConfirmationButtons: boolean;
}

export function McpEventMessage({
  event,
  shouldShowConfirmationButtons,
}: McpEventMessageProps) {
  return (
    <div>
      <GenericEventMessage
        title={getEventContent(event).title}
        details={
          <MCPObservationContent
            event={{ message: event.message, arguments: event.arguments }}
          />
        }
        success={getObservationResult(event)}
      />
      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
