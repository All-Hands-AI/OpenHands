import { ConversationTrigger } from "../open-hands.types";
import { Provider } from "#/types/settings";

// V1 API Types for requests
// Note: This represents the serialized API format, not the internal TextContent/ImageContent types
export interface V1MessageContent {
  type: "text" | "image_url";
  text?: string;
  image_url?: {
    url: string;
  };
}

type V1Role = "user" | "system" | "assistant" | "tool";

export interface V1SendMessageRequest {
  role: V1Role;
  content: V1MessageContent[];
}

export interface V1AppConversationStartRequest {
  sandbox_id?: string | null;
  initial_message?: V1SendMessageRequest | null;
  processors?: unknown[]; // EventCallbackProcessor - keeping as unknown for now
  llm_model?: string | null;
  selected_repository?: string | null;
  selected_branch?: string | null;
  git_provider?: Provider | null;
  title?: string | null;
  trigger?: ConversationTrigger | null;
  pr_number?: number[];
}

export type V1AppConversationStartTaskStatus =
  | "WORKING"
  | "WAITING_FOR_SANDBOX"
  | "PREPARING_REPOSITORY"
  | "RUNNING_SETUP_SCRIPT"
  | "SETTING_UP_GIT_HOOKS"
  | "STARTING_CONVERSATION"
  | "READY"
  | "ERROR";

export interface V1AppConversationStartTask {
  id: string;
  created_by_user_id: string | null;
  status: V1AppConversationStartTaskStatus;
  detail: string | null;
  app_conversation_id: string | null;
  sandbox_id: string | null;
  agent_server_url: string | null;
  request: V1AppConversationStartRequest;
  created_at: string;
  updated_at: string;
}

export interface V1SendMessageResponse {
  role: "user" | "system" | "assistant" | "tool";
  content: V1MessageContent[];
}

export interface V1AppConversationStartTaskPage {
  items: V1AppConversationStartTask[];
  next_page_id: string | null;
}

export type V1SandboxStatus =
  | "MISSING"
  | "STARTING"
  | "RUNNING"
  | "STOPPED"
  | "PAUSED";

export type V1AgentExecutionStatus =
  | "RUNNING"
  | "AWAITING_USER_INPUT"
  | "AWAITING_USER_CONFIRMATION"
  | "FINISHED"
  | "PAUSED"
  | "STOPPED";

export interface V1AppConversation {
  id: string;
  created_by_user_id: string | null;
  sandbox_id: string;
  selected_repository: string | null;
  selected_branch: string | null;
  git_provider: Provider | null;
  title: string | null;
  trigger: ConversationTrigger | null;
  pr_number: number[];
  llm_model: string | null;
  metrics: unknown | null;
  created_at: string;
  updated_at: string;
  sandbox_status: V1SandboxStatus;
  agent_status: V1AgentExecutionStatus | null;
  conversation_url: string | null;
  session_api_key: string | null;
}
