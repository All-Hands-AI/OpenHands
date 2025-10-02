import { OpenHandsEvent, ObservationEvent } from "./core";

/**
 * Type guard function to check if an event is an observation event
 */
export const isObservationEvent = (
  event: OpenHandsEvent,
): event is ObservationEvent =>
  event.source === "environment" &&
  "action_id" in event &&
  "observation" in event;
