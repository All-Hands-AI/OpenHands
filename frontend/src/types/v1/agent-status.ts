/**
 * V1 Agent Status enum matching backend AgentStatus
 */
export enum V1AgentStatus {
  IDLE = "idle",
  RUNNING = "running",
  PAUSED = "paused",
  WAITING_FOR_CONFIRMATION = "waiting_for_confirmation",
  FINISHED = "finished",
  ERROR = "error",
  STUCK = "stuck",
}

/**
 * Type guard to check if a value is a valid V1AgentStatus
 */
export function isV1AgentStatus(value: unknown): value is V1AgentStatus {
  return (
    typeof value === "string" &&
    Object.values(V1AgentStatus).includes(value as V1AgentStatus)
  );
}
