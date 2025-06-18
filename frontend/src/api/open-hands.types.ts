import { ConversationStatus } from "#/types/conversation-status";
import { RuntimeStatus } from "#/types/runtime-status";

export interface ErrorResponse {
  error: string;
}

export interface SaveFileSuccessResponse {
  message: string;
}

export interface FileUploadSuccessResponse {
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
  STRIPE_PUBLISHABLE_KEY?: string;
  FEATURE_FLAGS: {
    ENABLE_BILLING: boolean;
    HIDE_LLM_SETTINGS: boolean;
  };
}

export interface GetVSCodeUrlResponse {
  vscode_url: string | null;
  error?: string;
}

export interface GetTrajectoryResponse {
  trajectory: unknown[] | null;
  error?: string;
}

export interface AuthenticateResponse {
  message?: string;
  error?: string;
}

export type ConversationTrigger = "resolver" | "gui" | "suggested_task";

export interface Conversation {
  conversation_id: string;
  title: string;
  selected_repository: string | null;
  selected_branch: string | null;
  git_provider: string | null;
  last_updated_at: string;
  created_at: string;
  status: ConversationStatus;
  runtime_status: RuntimeStatus | null;
  trigger?: ConversationTrigger;
  url: string | null;
  session_api_key: string | null;
}

export interface ResultSet<T> {
  results: T[];
  next_page_id: string | null;
}

export type GitChangeStatus = "M" | "A" | "D" | "R" | "U";

export interface GitChange {
  status: GitChangeStatus;
  path: string;
}

export interface GitChangeDiff {
  modified: string;
  original: string;
}

export interface InputMetadata {
  name: string;
  description: string;
}

export interface Microagent {
  name: string;
  type: "repo" | "knowledge";
  content: string;
  triggers: string[];
}

export interface GetMicroagentsResponse {
  microagents: Microagent[];
}

export interface GetMicroagentPromptResponse {
  status: string;
  prompt: string;
}
