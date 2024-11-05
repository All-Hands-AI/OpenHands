type Message = {
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
};

type ErrorMessage = {
  error: boolean;
  id?: string;
  message: string;
};
