export enum MicroagentStatus {
  CREATING = "creating",
  COMPLETED = "completed",
  ERROR = "error",
}

export interface EventMicroagentStatus {
  eventId: number;
  conversationId: string;
  status: MicroagentStatus;
}
