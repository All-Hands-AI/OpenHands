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

export interface AuthenticationResponse {
  message: string;
  login?: string; // Only present when allow list is enabled
}

export interface Feedback {
  version: string;
  email: string;
  token: string;
  polarity: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}

export interface GetConfigResponse {
  APP_MODE: "saas" | "oss";
  APP_SLUG?: string;
  GITHUB_CLIENT_ID: string;
  POSTHOG_CLIENT_KEY: string;
}

export interface GetVSCodeUrlResponse {
  vscode_url: string | null;
  error?: string;
}

export interface AuthenticateResponse {
  message?: string;
  error?: string;
}
