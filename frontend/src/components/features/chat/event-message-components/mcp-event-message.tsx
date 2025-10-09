import { GenericEventMessage } from "../generic-event-message";
import { MCPObservationContent } from "../mcp-observation-content";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";
import { MCPToolObservation, ObservationEvent } from "#/types/v1/core";

interface McpEventMessageProps {
  event: ObservationEvent<MCPToolObservation>;
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
            event={{
              message: event.observation.content[0].text,
              arguments: event.observation.content[0].arguments,
            }}
          />
        }
        success={getObservationResult(event)}
      />
      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
