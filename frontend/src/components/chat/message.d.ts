type Message = {
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
};
