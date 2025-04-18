export type OpenHandsEventType =
  | "message"
  | "agent_state_changed"
  | "run"
  | "read"
  | "write"
  | "edit"
  | "run_ipython"
  | "delegate"
  | "browse"
  | "browse_interactive"
  | "reject"
  | "think"
  | "finish"
  | "error"
  | "recall";

interface OpenHandsBaseEvent {
  id: number;
  source: "agent" | "user";
  message: string;
  timestamp: string; // ISO 8601
}

export interface OpenHandsActionEvent<T extends OpenHandsEventType>
  extends OpenHandsBaseEvent {
  action: T;
  args: Record<string, unknown>;
}

export interface OpenHandsObservationEvent<T extends OpenHandsEventType>
  extends OpenHandsBaseEvent {
  cause: number;
  observation: T;
  content: string;
  extras: Record<string, unknown>;
}
