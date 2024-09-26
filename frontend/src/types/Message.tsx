export interface ActionMessage {
  // Either 'agent' or 'user'
  source: string;

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
  // TODO not implemented yet
  // Whether the status is an error, default is false
  is_error: boolean;

  // A status message to display to the user
  status: string;
}
