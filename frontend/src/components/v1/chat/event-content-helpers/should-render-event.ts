import { OpenHandsEvent } from "#/types/v1/core";
import {
  isActionEvent,
  isObservationEvent,
  isMessageEvent,
  isAgentErrorEvent,
  isConversationStateUpdateEvent,
} from "#/types/v1/type-guards";

// V1 events that should not be rendered
const NO_RENDER_ACTION_TYPES = [
  "ThinkAction",
  // Add more action types that should not be rendered
];

const NO_RENDER_OBSERVATION_TYPES = [
  "ThinkObservation",
  // Add more observation types that should not be rendered
];

export const shouldRenderEvent = (event: OpenHandsEvent) => {
  // Explicitly exclude system events that should not be rendered in chat
  if (isConversationStateUpdateEvent(event)) {
    return false;
  }

  // Render action events (with filtering)
  if (isActionEvent(event)) {
    // For V1, action is an object with kind property
    const actionType = event.action.kind;

    // Hide user commands from the chat interface
    if (actionType === "ExecuteBashAction" && event.source === "user") {
      return false;
    }

    return !NO_RENDER_ACTION_TYPES.includes(actionType);
  }

  // Render observation events (with filtering)
  if (isObservationEvent(event)) {
    // For V1, observation is an object with kind property
    const observationType = event.observation.kind;

    // Note: ObservationEvent source is always "environment", not "user"
    // So no need to check for user source here

    return !NO_RENDER_OBSERVATION_TYPES.includes(observationType);
  }

  // Render message events (user and assistant messages)
  if (isMessageEvent(event)) {
    return true;
  }

  // Render agent error events
  if (isAgentErrorEvent(event)) {
    return true;
  }

  // Don't render any other event types (system events, etc.)
  return false;
};

export const hasUserEvent = (events: OpenHandsEvent[]) =>
  events.some((event) => event.source === "user");
