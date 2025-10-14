import axios from "axios";
import { openHands } from "../open-hands-axios";
import { ConversationTrigger, GetVSCodeUrlResponse } from "../open-hands.types";
import { Provider } from "#/types/settings";
import { buildHttpBaseUrl } from "#/utils/websocket-url";

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

export interface V1SendMessageResponse {
  role: "user" | "system" | "assistant" | "tool";
  content: V1MessageContent[];
}

export interface V1AppConversationStartTaskPage {
  items: V1AppConversationStartTask[];
  next_page_id: string | null;
}

class V1ConversationService {
  /**
   * Send a message to a V1 conversation
   * @param conversationId The conversation ID
   * @param message The message to send
   * @returns The sent message response
   */
  static async sendMessage(
    conversationId: string,
    message: V1SendMessageRequest,
  ): Promise<V1SendMessageResponse> {
    const { data } = await openHands.post<V1SendMessageResponse>(
      `/api/conversations/${conversationId}/events`,
      message,
    );

    return data;
  }

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

  /**
   * Search for start tasks (ongoing tasks that haven't completed yet)
   * Use this to find tasks that were started but the user navigated away
   *
   * Note: Backend only supports filtering by limit. To filter by repository/trigger,
   * filter the results client-side after fetching.
   *
   * @param limit Maximum number of tasks to return (max 100)
   * @returns Array of start tasks
   */
  static async searchStartTasks(
    limit: number = 100,
  ): Promise<V1AppConversationStartTask[]> {
    const params = new URLSearchParams();
    params.append("limit", limit.toString());

    const { data } = await openHands.get<V1AppConversationStartTaskPage>(
      `/api/v1/app-conversations/start-tasks/search?${params.toString()}`,
    );

    return data.items;
  }

  /**
   * Get the VSCode URL for a V1 conversation
   * Uses the custom runtime URL from the conversation
   * Note: V1 endpoint doesn't require conversationId in the URL path - it's identified via session API key header
   *
   * @param _conversationId The conversation ID (not used in V1, kept for interface compatibility)
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param sessionApiKey Session API key for authentication (required for V1)
   * @returns VSCode URL response
   */
  static async getVSCodeUrl(
    _conversationId: string,
    conversationUrl: string | null | undefined,
    sessionApiKey?: string | null,
  ): Promise<GetVSCodeUrlResponse> {
    // Build the HTTP base URL from conversationUrl (same as WebSocket connection)
    const baseUrl = buildHttpBaseUrl(conversationUrl);

    // Add base_url query parameter to tell the backend what host:port to use
    // instead of defaulting to port 8001
    const url = `${baseUrl}/api/vscode/url`;

    // Add session API key header (required for V1 to identify conversation)
    const headers: Record<string, string> = {};
    if (sessionApiKey) {
      headers["X-Session-API-Key"] = sessionApiKey;
    }

    // V1 API returns {url: '...'} instead of {vscode_url: '...'}
    // Map it to match the expected interface
    const { data } = await axios.get<{ url: string | null }>(url, { headers });
    return {
      vscode_url: data.url,
    };
  }
}

export default V1ConversationService;
