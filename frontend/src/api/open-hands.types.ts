export interface ErrorResponse {
  error: string;
}

export interface SaveFileSuccessResponse {
  message: string;
}

export interface FileUploadSuccessResponse {
  message: string;
  uploaded_files: string[];
  skipped_files: { name: string; reason: string }[];
}

export interface FeedbackBodyResponse {
  message: string;
  feedback_id: string;
  password: string;
}

export interface FeedbackResponse {
  statusCode: number;
  body: FeedbackBodyResponse;
}

export interface GitHubAccessTokenResponse {
  access_token: string;
}

export interface Feedback {
  version: string;
  email: string;
  token: string;
  feedback: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}
