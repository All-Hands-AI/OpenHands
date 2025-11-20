import { BaseEvent } from "../base/event";
import { V1ExecutionStatus } from "../base/common";

/**
 * Conversation state value types
 */
export interface ConversationState {
  execution_status: V1ExecutionStatus;
  // Add other conversation state fields here as needed
}

interface ConversationStateUpdateEventBase extends BaseEvent {
  /**
   * The source is always "environment" for conversation state update events
   */
  source: "environment";

  /**
   * Unique key for this state update event.
   * Can be "full_state" for full state snapshots or field names for partial updates.
   */
  key: "full_state" | "execution_status"; // Extend with other keys as needed

  /**
   * Conversation state updates
   */
  value: ConversationState | V1ExecutionStatus;
}

// Narrowed interfaces for full state update event
export interface ConversationStateUpdateEventFullState
  extends ConversationStateUpdateEventBase {
  key: "full_state";
  value: ConversationState;
}

// Narrowed interface for agent status update event
export interface ConversationStateUpdateEventAgentStatus
  extends ConversationStateUpdateEventBase {
  key: "execution_status";
  value: V1ExecutionStatus;
}

// Conversation state update event - contains conversation state updates
export type ConversationStateUpdateEvent =
  | ConversationStateUpdateEventFullState
  | ConversationStateUpdateEventAgentStatus;

// Conversation error event - contains error information
export interface ConversationErrorEvent extends BaseEvent {
  /**
   * The source is always "environment" for conversation error events
   */
  source: "environment";

  /**
   * Error code (e.g., "AuthenticationError")
   */
  code: string;

  /**
   * Detailed error message
   */
  detail: string;
}
