type Message = {
  sender: "user" | "assistant";
  content: string;
  imageUrls: string[];
  timestamp: string;
  secondaryId: string;
};

type ErrorMessage = {
  error: boolean;
  id?: string;
  message: string;
};
