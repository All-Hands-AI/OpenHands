export interface BaseMessage {
  sender: "user" | "assistant";
  content: string;
  imageUrls?: string[];
  timestamp: string;
  pending?: boolean;
  translationID?: string;
  eventID?: string;
  success?: boolean;
  filePath?: string;
}

export interface ThoughtMessage extends BaseMessage {
  type: "thought";
}

export interface ActionMessage extends BaseMessage {
  type: "action";
  args: Record<string, unknown>;
}

export interface ErrorMessage extends BaseMessage {
  type: "error";
  id?: string;
}

export interface ObservationMessage extends BaseMessage {
  type: "observation";
  observation: string;
  extras: Record<string, unknown>;
}

export interface StatusMessage extends BaseMessage {
  type: "status" | "info";
  id?: string;
  message?: string;
}

export type Message =
  | ThoughtMessage
  | ActionMessage
  | ErrorMessage
  | ObservationMessage
  | StatusMessage;

export type AnyMessage = Message;
