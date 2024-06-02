import { request } from "./api";

export interface Feedback {
  version: string;
  email: string;
  token: string;
  feedback: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}

export async function sendFeedback(data: Feedback) {
  return request("/api/submit-feedback", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
}
