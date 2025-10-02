import { BaseEvent } from "../base/event";

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
   * Serialized conversation state updates.
   * For "full_state" key, this contains the complete conversation state.
   * For field-specific keys, this contains the updated field value.
   */
  value: unknown;
}
