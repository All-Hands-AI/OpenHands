import axios from "axios";
import { openHands } from "../open-hands-axios";
import { ConversationTrigger, GetVSCodeUrlResponse } from "../open-hands.types";
import { Provider } from "#/types/settings";
import { buildHttpBaseUrl } from "#/utils/websocket-url";
import type {
  V1SendMessageRequest,
  V1SendMessageResponse,
  V1AppConversationStartRequest,
  V1AppConversationStartTask,
  V1AppConversationStartTaskPage,
  V1AppConversation,
} from "./v1-conversation-service.types";

class V1ConversationService {
  /**
   * Build headers for V1 API requests that require session authentication
   * @param sessionApiKey Session API key for authentication
   * @returns Headers object with X-Session-API-Key if provided
   */
  private static buildSessionHeaders(
    sessionApiKey?: string | null,
  ): Record<string, string> {
    const headers: Record<string, string> = {};
    if (sessionApiKey) {
      headers["X-Session-API-Key"] = sessionApiKey;
    }
    return headers;
  }

  /**
   * Build the full URL for V1 runtime-specific endpoints
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param path The API path (e.g., "/api/vscode/url")
   * @returns Full URL to the runtime endpoint
   */
  private static buildRuntimeUrl(
    conversationUrl: string | null | undefined,
    path: string,
  ): string {
    const baseUrl = buildHttpBaseUrl(conversationUrl);
    return `${baseUrl}${path}`;
  }

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
    const url = this.buildRuntimeUrl(conversationUrl, "/api/vscode/url");
    const headers = this.buildSessionHeaders(sessionApiKey);

    // V1 API returns {url: '...'} instead of {vscode_url: '...'}
    // Map it to match the expected interface
    const { data } = await axios.get<{ url: string | null }>(url, { headers });
    return {
      vscode_url: data.url,
    };
  }

  /**
   * Pause a V1 conversation
   * Uses the custom runtime URL from the conversation
   *
   * @param conversationId The conversation ID
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param sessionApiKey Session API key for authentication (required for V1)
   * @returns Success response
   */
  static async pauseConversation(
    conversationId: string,
    conversationUrl: string | null | undefined,
    sessionApiKey?: string | null,
  ): Promise<{ success: boolean }> {
    const url = this.buildRuntimeUrl(
      conversationUrl,
      `/api/conversations/${conversationId}/pause`,
    );
    const headers = this.buildSessionHeaders(sessionApiKey);

    const { data } = await axios.post<{ success: boolean }>(
      url,
      {},
      { headers },
    );
    return data;
  }

  /**
   * Pause a V1 sandbox
   * Calls the /api/v1/sandboxes/{id}/pause endpoint
   *
   * @param sandboxId The sandbox ID to pause
   * @returns Success response
   */
  static async pauseSandbox(sandboxId: string): Promise<{ success: boolean }> {
    const { data } = await openHands.post<{ success: boolean }>(
      `/api/v1/sandboxes/${sandboxId}/pause`,
      {},
    );
    return data;
  }

  /**
   * Resume a V1 sandbox
   * Calls the /api/v1/sandboxes/{id}/resume endpoint
   *
   * @param sandboxId The sandbox ID to resume
   * @returns Success response
   */
  static async resumeSandbox(sandboxId: string): Promise<{ success: boolean }> {
    const { data } = await openHands.post<{ success: boolean }>(
      `/api/v1/sandboxes/${sandboxId}/resume`,
      {},
    );
    return data;
  }

  /**
   * Batch get V1 app conversations by their IDs
   * Returns null for any missing conversations
   *
   * @param ids Array of conversation IDs (max 100)
   * @returns Array of conversations or null for missing ones
   */
  static async batchGetAppConversations(
    ids: string[],
  ): Promise<(V1AppConversation | null)[]> {
    if (ids.length === 0) {
      return [];
    }
    if (ids.length > 100) {
      throw new Error("Cannot request more than 100 conversations at once");
    }

    const params = new URLSearchParams();
    ids.forEach((id) => params.append("ids", id));

    const { data } = await openHands.get<(V1AppConversation | null)[]>(
      `/api/v1/app-conversations?${params.toString()}`,
    );
    return data;
  }

  /**
   * Upload a single file to the V1 conversation workspace
   * V1 API endpoint: POST /api/file/upload/{path}
   *
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param sessionApiKey Session API key for authentication (required for V1)
   * @param file The file to upload
   * @param path The absolute path where the file should be uploaded (defaults to /workspace/{file.name})
   * @returns void on success, throws on error
   */
  static async uploadFile(
    conversationUrl: string | null | undefined,
    sessionApiKey: string | null | undefined,
    file: File,
    path?: string,
  ): Promise<void> {
    // Default to /workspace/{filename} if no path provided (must be absolute)
    const uploadPath = path || `/workspace/${file.name}`;
    const encodedPath = encodeURIComponent(uploadPath);
    const url = this.buildRuntimeUrl(
      conversationUrl,
      `/api/file/upload/${encodedPath}`,
    );
    const headers = this.buildSessionHeaders(sessionApiKey);

    // Create FormData with the file
    const formData = new FormData();
    formData.append("file", file);

    // Upload file
    await axios.post(url, formData, {
      headers: {
        ...headers,
        "Content-Type": "multipart/form-data",
      },
    });
  }
}

export default V1ConversationService;
