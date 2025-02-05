export interface Message {
  type: "thought" | "action" | "error";
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
