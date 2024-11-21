type Message = {
  type: "thought" | "error" | "action";
  id?: string;
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
};
