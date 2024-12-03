type Message = {
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
  pending?: boolean;
};

type ErrorMessage = {
  error: boolean;
  id?: string;
  message: string;
};
