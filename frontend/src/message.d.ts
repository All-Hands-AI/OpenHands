type Message = {
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  imageUrls?: string[];
  type?: "thought" | "error" | "action" | "browser_output";
  screenshot?: string;
  pending?: boolean;
  translationID?: string;
  eventID?: number;
};
