type Message = {
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
};

type ErrorMessage = {
  error: string;
  message: string;
};
