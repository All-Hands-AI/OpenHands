import { openHands } from "../open-hands-axios";
import { ConversationTrigger } from "../open-hands.types";
import { Provider } from "#/types/settings";

// V1 API Types for requests
export interface V1MessageContent {
  type: "text" | "image_url";
  text?: string;
  image_url?: {
    url: string;
  };
}

export interface V1SendMessageRequest {
  role: "user" | "system" | "assistant" | "tool";
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

class V1ConversationService {
  /**
   * Create a new V1 conversation using the app-conversations API
   * Returns the start task immediately with app_conversation_id as null.
   * You must poll getStartTask() until status is READY to get the conversation ID.
   *
   * @returns AppConversationStartTask with task ID
   */
  static async createConversation(
    selectedRepository?: string,
    git_provider?: Provider,
    initialUserMsg?: string,
    selected_branch?: string,
    conversationInstructions?: string,
    trigger?: ConversationTrigger,
  ): Promise<V1AppConversationStartTask> {
    const body: V1AppConversationStartRequest = {
      selected_repository: selectedRepository,
      git_provider,
      selected_branch,
      title: conversationInstructions,
      trigger,
    };

    // Add initial message if provided
    if (initialUserMsg) {
      body.initial_message = {
        role: "user",
        content: [
          {
            type: "text",
            text: initialUserMsg,
          },
        ],
      };
    }

    const { data } = await openHands.post<V1AppConversationStartTask>(
      "/api/v1/app-conversations",
      body,
    );

    return data;
  }

  /**
   * Get a start task by ID
   * Poll this endpoint until status is READY to get the app_conversation_id
   *
   * @param taskId The task UUID
   * @returns AppConversationStartTask or null
   */
  static async getStartTask(
    taskId: string,
  ): Promise<V1AppConversationStartTask | null> {
    const { data } = await openHands.get<(V1AppConversationStartTask | null)[]>(
      `/api/v1/app-conversations/start-tasks?ids=${taskId}`,
    );

    return data[0] || null;
  }
}

export default V1ConversationService;
