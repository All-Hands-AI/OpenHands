import { BaseEvent } from "../base/event";
import { V1AgentStatus } from "../../agent-status";

/**
 * Conversation state value types
 */
export interface ConversationState {
  agent_status: V1AgentStatus;
  // Add other conversation state fields here as needed
}

// Conversation state update event - contains conversation state updates
export interface ConversationStateUpdateEvent extends BaseEvent {
  /**
   * The source is always "environment" for conversation state update events
   */
  source: "environment";

  /**
   * Unique key for this state update event.
   * Can be "full_state" for full state snapshots or field names for partial updates.
   */
  key: string;

  /**
   * Conversation state updates
   */
  value: ConversationState;
}
