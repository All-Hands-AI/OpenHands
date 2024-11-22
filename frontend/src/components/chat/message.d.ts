type Message = {
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  type?: "thought" | "error" | "action";
  id?: string;
  eventID?: int;
  imageUrls?: string[];
};
