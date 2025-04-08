export type DevEventType =
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

interface DevBaseEvent {
  id: number;
  source: "agent" | "user";
  message: string;
  timestamp: string; // ISO 8601
}

export interface DevActionEvent<T extends DevEventType>
  extends DevBaseEvent {
  action: T;
  args: Record<string, unknown>;
}

export interface DevObservationEvent<T extends DevEventType>
  extends DevBaseEvent {
  cause: number;
  observation: T;
  content: string;
  extras: Record<string, unknown>;
}
