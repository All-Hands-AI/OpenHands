export interface FeedbackData {
  email: string;
  token: string;
  feedback: "positive" | "negative";
  trajectory: unknown[];
}

export const sendFeedback = async (data: FeedbackData) =>
  fetch(
    "https://kttkfkoju5.execute-api.us-east-2.amazonaws.com/od-share-trajectory",
    {
      method: "POST",
      mode: "no-cors",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
  );
