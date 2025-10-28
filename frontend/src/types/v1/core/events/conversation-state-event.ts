import { BaseEvent } from "../base/event";
import { V1AgentStatus } from "../base/common";

/**
 * Conversation state value types
 */
export interface ConversationState {
  agent_status: V1AgentStatus;
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
  key: "full_state" | "agent_status"; // Extend with other keys as needed

  /**
   * Conversation state updates
   */
  value: ConversationState | V1AgentStatus;
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
  key: "agent_status";
  value: V1AgentStatus;
}

// Conversation state update event - contains conversation state updates
export type ConversationStateUpdateEvent =
  | ConversationStateUpdateEventFullState
  | ConversationStateUpdateEventAgentStatus;
