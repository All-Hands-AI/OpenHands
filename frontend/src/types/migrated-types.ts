// This file exports types that were previously defined in Redux slices
// but are now used in React Query hooks

// From security-analyzer-slice.ts
export enum ActionSecurityRisk {
  UNKNOWN = -1,
  LOW = 0,
  MEDIUM = 1,
  HIGH = 2,
}

export type SecurityAnalyzerLog = {
  id: number;
  content: string;
  security_risk: ActionSecurityRisk;
  confirmation_state?: "awaiting_confirmation" | "confirmed" | "rejected";
  confirmed_changed: boolean;
};

// From jupyter-slice.ts
export type Cell = {
  content: string;
  type: "input" | "output";
};

// From command-slice.ts
export type Command = {
  content: string;
  type: "input" | "output";
};

// Export actions that were previously in chat-slice.ts
export const addUserMessage = (payload: {
  content: string;
  imageUrls: string[];
  timestamp: string;
  pending?: boolean;
}) => ({
  type: "chat/addUserMessage",
  payload,
});

export const addAssistantMessage = (content: string) => ({
  type: "chat/addAssistantMessage",
  payload: content,
});

export const addAssistantAction = (action: unknown) => ({
  type: "chat/addAssistantAction",
  payload: action,
});

export const addAssistantObservation = (observation: unknown) => ({
  type: "chat/addAssistantObservation",
  payload: observation,
});

export const addErrorMessage = (payload: { id?: string; message: string }) => ({
  type: "chat/addErrorMessage",
  payload,
});

export const clearMessages = () => ({
  type: "chat/clearMessages",
});

// Export actions that were previously in command-slice.ts
export const appendInput = (payload: { id: string; input: string }) => ({
  type: "cmd/appendInput",
  payload,
});

export const appendOutput = (payload: {
  id: string;
  output: string;
  isExecuting?: boolean;
  exitCode?: number | null;
}) => ({
  type: "cmd/appendOutput",
  payload,
});

// Export actions that were previously in security-analyzer-slice.ts
export const appendSecurityAnalyzerInput = (payload: unknown) => ({
  type: "securityAnalyzer/appendSecurityAnalyzerInput",
  payload,
});