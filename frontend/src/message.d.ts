export type Message = {
  sender: "user" | "assistant";
  agentName?: string;
  content: string;
  timestamp: string;
  imageUrls?: string[];
  type?: "thought" | "error" | "action";
  success?: boolean;
  pending?: boolean;
  translationID?: string;
  eventID?: number;
};
