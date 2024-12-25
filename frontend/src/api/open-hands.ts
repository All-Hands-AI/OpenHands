import {
  SaveFileSuccessResponse,
  FileUploadSuccessResponse,
  Feedback,
  FeedbackResponse,
  GitHubAccessTokenResponse,
  ErrorResponse,
  GetConfigResponse,
  GetVSCodeUrlResponse,
  AuthenticateResponse,
} from "./open-hands.types";
import { openHands } from "./open-hands-axios";

class OpenHands {
  /**
   * Retrieve the list of models available
   * @returns List of models available
   */
  static async getModels(): Promise<string[]> {
    const { data } = await openHands.get<string[]>("/api/options/models");
    return data;
  }

  /**
   * Retrieve the list of agents available
   * @returns List of agents available
   */
  static async getAgents(): Promise<string[]> {
    const { data } = await openHands.get<string[]>("/api/options/agents");
    return data;
  }

  /**
   * Retrieve the list of security analyzers available
   * @returns List of security analyzers available
   */
  static async getSecurityAnalyzers(): Promise<string[]> {
    const { data } = await openHands.get<string[]>(
      "/api/options/security-analyzers",
    );
    return data;
  }

  static async getConfig(): Promise<GetConfigResponse> {
    const { data } = await openHands.get<GetConfigResponse>(
      "/api/options/config",
    );
    return data;
  }

  /**
   * Retrieve the list of files available in the workspace
   * @param path Path to list files from
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  static async getFiles(
    conversationId: string,
    path?: string,
  ): Promise<string[]> {
    const url = `/api/conversations/${conversationId}/list-files`;
    const { data } = await openHands.get<string[]>(url, {
      params: { path },
    });
    return data;
  }

  /**
   * Retrieve the content of a file
   * @param path Full path of the file to retrieve
   * @returns Content of the file
   */
  static async getFile(conversationId: string, path: string): Promise<string> {
    const url = `/api/conversations/${conversationId}/select-file`;
    const { data } = await openHands.get<{ code: string }>(url, {
      params: { file: path },
    });

    return data.code;
  }

  /**
   * Save the content of a file
   * @param path Full path of the file to save
   * @param content Content to save in the file
   * @returns Success message or error message
   */
  static async saveFile(
    conversationId: string,
    path: string,
    content: string,
  ): Promise<SaveFileSuccessResponse> {
    const url = `/api/conversations/${conversationId}/save-file`;
    const { data } = await openHands.post<
      SaveFileSuccessResponse | ErrorResponse
    >(url, {
      filePath: path,
      content,
    });

    if ("error" in data) throw new Error(data.error);
    return data;
  }

  /**
   * Upload a file to the workspace
   * @param file File to upload
   * @returns Success message or error message
   */
  static async uploadFiles(
    conversationId: string,
    files: File[],
  ): Promise<FileUploadSuccessResponse> {
    const url = `/api/conversations/${conversationId}/upload-files`;
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const { data } = await openHands.post<
      FileUploadSuccessResponse | ErrorResponse
    >(url, formData);

    if ("error" in data) throw new Error(data.error);
    return data;
  }

  /**
   * Send feedback to the server
   * @param data Feedback data
   * @returns The stored feedback data
   */
  static async submitFeedback(
    conversationId: string,
    feedback: Feedback,
  ): Promise<FeedbackResponse> {
    const url = `/api/conversations/${conversationId}/submit-feedback`;
    const { data } = await openHands.post<FeedbackResponse>(url, feedback);
    return data;
  }

  /**
   * Authenticate with GitHub token
   * @returns Response with authentication status and user info if successful
   */
  static async authenticate(
    appMode: GetConfigResponse["APP_MODE"],
  ): Promise<boolean> {
    if (appMode === "oss") return true;

    const response =
      await openHands.post<AuthenticateResponse>("/api/authenticate");
    return response.status === 200;
  }

  /**
   * Refresh Github Token
   * @returns Refreshed Github access token
   */
  static async refreshToken(
    appMode: GetConfigResponse["APP_MODE"],
    userId: string,
  ): Promise<string> {
    if (appMode === "oss") return "";

    const response = await openHands.post<GitHubAccessTokenResponse>(
      "/api/refresh-token",
      {
        userId,
      },
    );
    return response.data.access_token;
  }

  /**
   * Get the blob of the workspace zip
   * @returns Blob of the workspace zip
   */
  static async getWorkspaceZip(conversationId: string): Promise<Blob> {
    const url = `/api/conversations/${conversationId}/zip-directory`;
    const response = await openHands.get(url, {
      responseType: "blob",
    });
    return response.data;
  }

  /**
   * @param code Code provided by GitHub
   * @returns GitHub access token
   */
  static async getGitHubAccessToken(
    code: string,
  ): Promise<GitHubAccessTokenResponse> {
    const { data } = await openHands.post<GitHubAccessTokenResponse>(
      "/api/github/callback",
      {
        code,
      },
    );
    return data;
  }

  /**
   * Get the VSCode URL
   * @returns VSCode URL
   */
  static async getVSCodeUrl(
    conversationId: string,
  ): Promise<GetVSCodeUrlResponse> {
    const { data } = await openHands.get<GetVSCodeUrlResponse>(
      `/api/conversations/${conversationId}/vscode-url`,
    );
    return data;
  }

  static async getRuntimeId(
    conversationId: string,
  ): Promise<{ runtime_id: string }> {
    const { data } = await openHands.get<{ runtime_id: string }>(
      `/api/conversations/${conversationId}/config`,
    );
    return data;
  }

  static async searchEvents(
    conversationId: string,
    params: {
      query?: string;
      startId?: number;
      limit?: number;
      eventType?: string;
      source?: string;
      startDate?: string;
      endDate?: string;
    },
  ): Promise<{ events: Record<string, unknown>[]; has_more: boolean }> {
    const { data } = await openHands.get<{
      events: Record<string, unknown>[];
      has_more: boolean;
    }>(`/api/conversations/${conversationId}/events/search`, {
      params: {
        query: params.query,
        start_id: params.startId,
        limit: params.limit,
        event_type: params.eventType,
        source: params.source,
        start_date: params.startDate,
        end_date: params.endDate,
      },
    });
    return data;
  }

  static async newConversation(params: {
    githubToken?: string;
    args?: Record<string, unknown>;
    selectedRepository?: string;
  }): Promise<{ conversation_id: string }> {
    const { data } = await openHands.post<{
      conversation_id: string;
    }>("/api/conversations", {
      github_token: params.githubToken,
      args: params.args,
      selected_repository: params.selectedRepository,
    });
    // TODO: remove this once we have a multi-conversation UI
    localStorage.setItem("latest_conversation_id", data.conversation_id);
    return data;
  }
}

export default OpenHands;
