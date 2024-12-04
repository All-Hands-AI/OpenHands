type Message = {
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  imageUrls?: string[];
  type?: "thought" | "error" | "action";
  pending?: boolean;
  translationID?: string;
  eventID?: number;
};
