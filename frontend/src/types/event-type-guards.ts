import type { OpenHandsEvent } from "./v1/core/openhands-event";
import type { OpenHandsParsedEvent } from "./core/index";

/**
 * Type guard to check if an event is a V1 OpenHandsEvent
 */
export function isV1Event(
  event: OpenHandsEvent | OpenHandsParsedEvent,
): event is OpenHandsEvent {
  // Handle null/undefined cases
  if (!event || typeof event !== "object") {
    return false;
  }

  // V1 events have string IDs (ULID/UUID), V0 events have numeric IDs
  return "id" in event && typeof event.id === "string";
}

/**
 * Type guard to check if an event is a V0 OpenHandsParsedEvent
 */
export function isV0Event(
  event: OpenHandsEvent | OpenHandsParsedEvent,
): event is OpenHandsParsedEvent {
  // Handle null/undefined cases
  if (!event || typeof event !== "object") {
    return false;
  }

  // V0 events have numeric IDs and either 'action' or 'observation' properties
  return (
    "id" in event &&
    typeof event.id === "number" &&
    ("action" in event || "observation" in event)
  );
}
