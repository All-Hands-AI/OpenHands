import { AxiosHeaders } from "axios";
import {
  Feedback,
  FeedbackResponse,
  GitHubAccessTokenResponse,
  GetConfigResponse,
  GetVSCodeUrlResponse,
  AuthenticateResponse,
  Conversation,
  ResultSet,
  GetTrajectoryResponse,
  GitChangeDiff,
  GitChange,
} from "./open-hands.types";
import { openHands } from "./open-hands-axios";
import { ApiSettings, PostApiSettings, Provider } from "#/types/settings";
import { GitUser, GitRepository, Branch } from "#/types/git";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";

class OpenHands {
  private static conversationUrl: string | null = null;

  private static sessionApiKey: string | null = null;

  /**
   * Set a custom conversation URL to use instead of the default
   * @param url Custom URL to use for conversation endpoints
   */
  static setConversationUrl(url: string | null): void {
    this.conversationUrl = url;
  }

  /**
   * Get the current custom conversation URL if set
   * @returns The custom conversation URL or null if not set
   */
  static getConversationUrl(): string | null {
    return this.conversationUrl;
  }

  /**
   * Set an API Key to be included in endpoint requests
   * @param key Custom API Key for conversation endpoints
   */
  static setSessionApiKey(key: string | null): void {
    this.sessionApiKey = key;
  }

  /**
   * Get the API Key to be included in endpoint requests
   * @return Custom API Key for conversation endpoints
   */
  static getSessionApiKey(): string | null {
    return this.sessionApiKey;
  }

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

  static getHeaders(): AxiosHeaders {
    const headers = new AxiosHeaders();
    if (this.sessionApiKey) {
      headers.set("X-Session-API-Key", this.sessionApiKey);
    }
    return headers;
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

    // Just make the request, if it succeeds (no exception thrown), return true
    await openHands.post<AuthenticateResponse>("/api/authenticate");
    return true;
  }

  /**
   * Get the blob of the workspace zip
   * @returns Blob of the workspace zip
   */
  static async getWorkspaceZip(conversationId: string): Promise<Blob> {
    const baseUrl =
      this.conversationUrl || `/api/conversations/${conversationId}`;
    const url = `${baseUrl}/zip-directory`;
    const response = await openHands.get(url, {
      responseType: "blob",
      headers: this.getHeaders(),
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
      "/api/keycloak/callback",
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
    const baseUrl =
      this.conversationUrl || `/api/conversations/${conversationId}`;
    const { data } = await openHands.get<GetVSCodeUrlResponse>(
      `${baseUrl}/vscode-url`,
      {
        headers: this.getHeaders(),
      },
    );
    return data;
  }

  static async getRuntimeId(
    conversationId: string,
  ): Promise<{ runtime_id: string }> {
    const baseUrl =
      this.conversationUrl || `/api/conversations/${conversationId}`;
    const { data } = await openHands.get<{ runtime_id: string }>(
      `${baseUrl}/config`,
      {
        headers: this.getHeaders(),
      },
    );
    return data;
  }

  static async getUserConversations(): Promise<Conversation[]> {
    const { data } = await openHands.get<ResultSet<Conversation>>(
      "/api/conversations?limit=20",
    );
    return data.results;
  }

  static async deleteUserConversation(conversationId: string): Promise<void> {
    await openHands.delete(`/api/conversations/${conversationId}`);
  }

  static async createConversation(
    selectedRepository?: string,
    git_provider?: Provider,
    initialUserMsg?: string,
    imageUrls?: string[],
    replayJson?: string,
    suggested_task?: SuggestedTask,
    selected_branch?: string,
  ): Promise<Conversation> {
    const body = {
      repository: selectedRepository,
      git_provider,
      selected_branch,
      initial_user_msg: initialUserMsg,
      image_urls: imageUrls,
      replay_json: replayJson,
      suggested_task,
    };

    const { data } = await openHands.post<Conversation>(
      "/api/conversations",
      body,
    );

    return data;
  }

  static async getConversation(
    conversationId: string,
  ): Promise<Conversation | null> {
    const { data } = await openHands.get<Conversation | null>(
      `/api/conversations/${conversationId}`,
    );

    return data;
  }

  /**
   * Get the settings from the server or use the default settings if not found
   */
  static async getSettings(): Promise<ApiSettings> {
    const { data } = await openHands.get<ApiSettings>("/api/settings");
    return data;
  }

  /**
   * Save the settings to the server. Only valid settings are saved.
   * @param settings - the settings to save
   */
  static async saveSettings(
    settings: Partial<PostApiSettings>,
  ): Promise<boolean> {
    const data = await openHands.post("/api/settings", settings);
    return data.status === 200;
  }

  static async createCheckoutSession(amount: number): Promise<string> {
    const { data } = await openHands.post(
      "/api/billing/create-checkout-session",
      {
        amount,
      },
    );
    return data.redirect_url;
  }

  static async createBillingSessionResponse(): Promise<string> {
    const { data } = await openHands.post(
      "/api/billing/create-customer-setup-session",
    );
    return data.redirect_url;
  }

  static async getBalance(): Promise<string> {
    const { data } = await openHands.get<{ credits: string }>(
      "/api/billing/credits",
    );
    return data.credits;
  }

  static async getGitUser(): Promise<GitUser> {
    const response = await openHands.get<GitUser>("/api/user/info");

    const { data } = response;

    const user: GitUser = {
      id: data.id,
      login: data.login,
      avatar_url: data.avatar_url,
      company: data.company,
      name: data.name,
      email: data.email,
    };

    return user;
  }

  static async searchGitRepositories(
    query: string,
    per_page = 5,
  ): Promise<GitRepository[]> {
    const response = await openHands.get<GitRepository[]>(
      "/api/user/search/repositories",
      {
        params: {
          query,
          per_page,
        },
      },
    );

    return response.data;
  }

  static async getTrajectory(
    conversationId: string,
  ): Promise<GetTrajectoryResponse> {
    const baseUrl =
      this.conversationUrl || `/api/conversations/${conversationId}`;
    const { data } = await openHands.get<GetTrajectoryResponse>(
      `${baseUrl}/trajectory`,
      {
        headers: this.getHeaders(),
      },
    );
    return data;
  }

  static async logout(appMode: GetConfigResponse["APP_MODE"]): Promise<void> {
    const endpoint =
      appMode === "saas" ? "/api/logout" : "/api/unset-provider-tokens";
    await openHands.post(endpoint);
  }

  static async getGitChanges(conversationId: string): Promise<GitChange[]> {
    const baseUrl =
      this.conversationUrl || `/api/conversations/${conversationId}`;
    const { data } = await openHands.get<GitChange[]>(
      `${baseUrl}/git/changes`,
      {
        headers: this.getHeaders(),
      },
    );
    return data;
  }

  static async getGitChangeDiff(
    conversationId: string,
    path: string,
  ): Promise<GitChangeDiff> {
    const baseUrl =
      this.conversationUrl || `/api/conversations/${conversationId}`;
    const { data } = await openHands.get<GitChangeDiff>(`${baseUrl}/git/diff`, {
      params: { path },
      headers: this.getHeaders(),
    });
    return data;
  }

  /**
   * Given a PAT, retrieves the repositories of the user
   * @returns A list of repositories
   */
  static async retrieveUserGitRepositories() {
    const { data } = await openHands.get<GitRepository[]>(
      "/api/user/repositories",
      {
        params: {
          sort: "pushed",
        },
      },
    );

    return data;
  }

  static async getRepositoryBranches(repository: string): Promise<Branch[]> {
    const { data } = await openHands.get<Branch[]>(
      `/api/user/repository/branches?repository=${encodeURIComponent(repository)}`,
    );

    return data;
  }
}

export default OpenHands;
