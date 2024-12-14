export interface ActionMessage {
  id: number;

  // Either 'agent' or 'user'
  source: "agent" | "user";

  // The action to be taken
  action: string;

  // The arguments for the action
  args: Record<string, string>;

  // A friendly message that can be put in the chat log
  message: string;

  // The timestamp of the message
  timestamp: string;
}

export interface ObservationMessage {
  // The type of observation
  observation: string;

  id: number;
  cause: number;

  // The observed data
  content: string;

  // Additional structured data
  extras: Record<string, string>;

  // A friendly message that can be put in the chat log
  message: string;

  // The timestamp of the message
  timestamp: string;
}

export interface StatusMessage {
  status_update: true;
  type: string;
  id: string;
  message: string;
}
