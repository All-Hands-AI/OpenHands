export enum MicroagentStatus {
  CREATING = "creating",
  RUNNING = "running",
  COMPLETED = "completed",
  ERROR = "error",
}

export interface EventMicroagentStatus {
  eventId: number;
  conversationId: string;
  status: MicroagentStatus;
}
