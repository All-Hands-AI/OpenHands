type Message = {
  type: "thought" | "error" | "action";
  id?: string;
  eventID?: int;
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
};
