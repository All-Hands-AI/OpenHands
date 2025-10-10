import { ConversationStatus } from "#/types/conversation-status";
import { RuntimeStatus } from "#/types/runtime-status";
import { Provider } from "#/types/settings";

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

export interface GetVSCodeUrlResponse {
  vscode_url: string | null;
  error?: string;
}

export interface GetTrajectoryResponse {
  trajectory: unknown[] | null;
  error?: string;
}

export interface RepositorySelection {
  selected_repository: string | null;
  selected_branch: string | null;
  git_provider: Provider | null;
}

export type ConversationTrigger =
  | "resolver"
  | "gui"
  | "suggested_task"
  | "microagent_management";

export interface Conversation {
  conversation_id: string;
  title: string;
  selected_repository: string | null;
  selected_branch: string | null;
  git_provider: Provider | null;
  last_updated_at: string;
  created_at: string;
  status: ConversationStatus;
  runtime_status: RuntimeStatus | null;
  trigger?: ConversationTrigger;
  url: string | null;
  session_api_key: string | null;
  pr_number?: number[] | null;
  conversation_version: "V0" | "V1";
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

export interface IOption<T> {
  label: string;
  value: T;
}

export interface CreateMicroagent {
  repo: string;
  git_provider?: Provider;
  title?: string;
}

export interface MicroagentContentResponse {
  content: string;
  path: string;
  git_provider: Provider;
  triggers: string[];
}

export type GetFilesResponse = string[];

export interface GetFileResponse {
  code: string;
}

// App Conversation Types
export interface SendMessageRequest {
  message: string;
  image_urls?: string[];
}

export interface EventCallbackProcessor {
  type: string;
  config: Record<string, unknown>;
}

export interface AppConversationStartRequest {
  sandbox_id?: string | null;
  initial_message?: SendMessageRequest | null;
  processors?: EventCallbackProcessor[];
  llm_model?: string | null;
  selected_repository?: string | null;
  selected_branch?: string | null;
  git_provider?: Provider | null;
  title?: string | null;
  trigger?: ConversationTrigger | null;
  pr_number?: number[];
}

export type AppConversationStartTaskStatus =
  | "WORKING"
  | "WAITING_FOR_SANDBOX"
  | "PREPARING_REPOSITORY"
  | "RUNNING_SETUP_SCRIPT"
  | "SETTING_UP_GIT_HOOKS"
  | "STARTING_CONVERSATION"
  | "READY"
  | "ERROR";

export interface AppConversationStartTask {
  id: string;
  created_by_user_id: string | null;
  status: AppConversationStartTaskStatus;
  detail?: string | null;
  app_conversation_id?: string | null;
  sandbox_id?: string | null;
  agent_server_url?: string | null;
  request: AppConversationStartRequest;
  created_at: string;
  updated_at: string;
}
