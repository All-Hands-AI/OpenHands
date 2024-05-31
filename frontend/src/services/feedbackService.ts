import { request } from "./api";

export interface FeedbackData {
  email: string;
  token: string;
  feedback: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}

export async function sendFeedback(data: FeedbackData) {
  await request("/api/submit-feedback", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
