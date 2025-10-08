import { OpenHandsEvent, ObservationEvent, BaseEvent } from "./core";
import { AgentErrorEvent } from "./core/events/observation-event";
import { MessageEvent } from "./core/events/message-event";
import { ActionEvent } from "./core/events/action-event";
import type { OpenHandsParsedEvent } from "../core/index";

/**
 * Type guard to check if an unknown value is a valid BaseEvent
 * @param value - The value to check
 * @returns true if the value is a valid BaseEvent
 */
export function isBaseEvent(value: unknown): value is BaseEvent {
  return (
    value !== null &&
    typeof value === "object" &&
    "id" in value &&
    "timestamp" in value &&
    "source" in value &&
    typeof value.id === "string" &&
    value.id.length > 0 &&
    typeof value.timestamp === "string" &&
    value.timestamp.length > 0 &&
    typeof value.source === "string" &&
    (value.source === "agent" ||
      value.source === "user" ||
      value.source === "environment")
  );
}

/**
 * Type guard function to check if an event is an observation event
 */
export const isObservationEvent = (
  event: OpenHandsEvent,
): event is ObservationEvent =>
  event.source === "environment" &&
  "action_id" in event &&
  "observation" in event;

/**
 * Type guard function to check if an event is an agent error event
 */
export const isAgentErrorEvent = (
  event: OpenHandsEvent,
): event is AgentErrorEvent =>
  event.source === "agent" &&
  "tool_name" in event &&
  "tool_call_id" in event &&
  "error" in event &&
  typeof event.tool_name === "string" &&
  typeof event.tool_call_id === "string" &&
  typeof event.error === "string";

/**
 * Type guard function to check if an event is a user message event
 */
export const isUserMessageEvent = (
  event: OpenHandsEvent,
): event is MessageEvent =>
  "llm_message" in event &&
  typeof event.llm_message === "object" &&
  event.llm_message !== null &&
  "role" in event.llm_message &&
  event.llm_message.role === "user";

/**
 * Type guard function to check if an event is an action event
 */
export const isActionEvent = (event: OpenHandsEvent): event is ActionEvent =>
  event.source === "agent" &&
  "action" in event &&
  "tool_name" in event &&
  "tool_call_id" in event &&
  typeof event.tool_name === "string" &&
  typeof event.tool_call_id === "string";

// =============================================================================
// TEMPORARY COMPATIBILITY TYPE GUARDS
// These will be removed once we fully migrate to V1 events
// =============================================================================

/**
 * TEMPORARY: Type guard to check if an event is a V1 OpenHandsEvent
 * Uses isBaseEvent to validate the complete event structure
 *
 * @deprecated This is temporary until full V1 migration is complete
 */
export function isV1Event(
  event: OpenHandsEvent | OpenHandsParsedEvent,
): event is OpenHandsEvent {
  // Use isBaseEvent to validate the complete BaseEvent structure
  // This ensures the event has all required properties with correct types
  return isBaseEvent(event);
}

/**
 * TEMPORARY: Type guard to check if an event is a V0 OpenHandsParsedEvent
 *
 * @deprecated This is temporary until full V1 migration is complete
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
