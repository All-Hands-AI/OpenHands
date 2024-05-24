export interface FeedbackData {
  email: string;
  token: string;
  feedback: "positive" | "negative";
  trajectory: unknown[];
}


export const sendFeedback = async (data: FeedbackData) =>
  fetch("/api/submit_feedback", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

