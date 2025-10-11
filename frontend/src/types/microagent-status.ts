export enum MicroagentStatus {
  WAITING = "waiting",
  CREATING = "creating",
  COMPLETED = "completed",
  ERROR = "error",
}

export interface EventMicroagentStatus {
  eventId: string;
  conversationId: string;
  status: MicroagentStatus;
  prUrl?: string; // Optional PR URL for completed status
}
