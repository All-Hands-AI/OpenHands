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
  GetMicroagentsResponse,
  GetMicroagentPromptResponse,
  CreateMicroagent,
  MicroagentContentResponse,
  FileUploadSuccessResponse,
  GetFilesResponse,
  GetFileResponse,
} from "./open-hands.types";
import { openHands } from "./open-hands-axios";
import { ApiSettings, PostApiSettings, Provider } from "#/types/settings";
import { GitUser, GitRepository, Branch } from "#/types/git";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";
import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { RepositoryMicroagent } from "#/types/microagent-management";
import { BatchFeedbackData } from "#/hooks/query/use-batch-feedback";

class OpenHands {
  private static currentConversation: Conversation | null = null;

  /**
   * Get a current conversation
   * @return the current conversation
   */
  static getCurrentConversation(): Conversation | null {
    return this.currentConversation;
  }

  /**
   * Set a current conversation
   * @param url Custom URL to use for conversation endpoints
   */
  static setCurrentConversation(
    currentConversation: Conversation | null,
  ): void {
    this.currentConversation = currentConversation;
  }

  /**
   * Get the url for the conversation. If
   */
  static getConversationUrl(conversationId: string): string {
    if (this.currentConversation?.conversation_id === conversationId) {
      if (this.currentConversation.url) {
        return this.currentConversation.url;
      }
    }
    return `/api/conversations/${conversationId}`;
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

  static getConversationHeaders(): AxiosHeaders {
    const headers = new AxiosHeaders();
    const sessionApiKey = this.currentConversation?.session_api_key;
    if (sessionApiKey) {
      headers.set("X-Session-API-Key", sessionApiKey);
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
   * Submit conversation feedback with rating
   * @param conversationId The conversation ID
   * @param rating The rating (1-5)
   * @param eventId Optional event ID this feedback corresponds to
   * @param reason Optional reason for the rating
   * @returns Response from the feedback endpoint
   */
  static async submitConversationFeedback(
    conversationId: string,
    rating: number,
    eventId?: number,
    reason?: string,
  ): Promise<{ status: string; message: string }> {
    const url = `/feedback/conversation`;
    const payload = {
      conversation_id: conversationId,
      event_id: eventId,
      rating,
      reason,
      metadata: { source: "likert-scale" },
    };
    const { data } = await openHands.post<{ status: string; message: string }>(
      url,
      payload,
    );
    return data;
  }

  /**
   * Check if feedback exists for a specific conversation and event
   * @param conversationId The conversation ID
   * @param eventId The event ID to check
   * @returns Feedback data including existence, rating, and reason
   */
  static async checkFeedbackExists(
    conversationId: string,
    eventId: number,
  ): Promise<{ exists: boolean; rating?: number; reason?: string }> {
    try {
      const url = `/feedback/conversation/${conversationId}/${eventId}`;
      const { data } = await openHands.get<{
        exists: boolean;
        rating?: number;
        reason?: string;
      }>(url);
      return data;
    } catch (error) {
      // Error checking if feedback exists
      return { exists: false };
    }
  }

  /**
   * Get feedback for multiple events in a conversation
   * @param conversationId The conversation ID
   * @returns Map of event IDs to feedback data including existence, rating, reason and metadata
   */
  static async getBatchFeedback(conversationId: string): Promise<
    Record<
      string,
      {
        exists: boolean;
        rating?: number;
        reason?: string;
        metadata?: Record<string, BatchFeedbackData>;
      }
    >
  > {
    const url = `/feedback/conversation/${conversationId}/batch`;
    const { data } = await openHands.get<
      Record<
        string,
        {
          exists: boolean;
          rating?: number;
          reason?: string;
          metadata?: Record<string, BatchFeedbackData>;
        }
      >
    >(url);

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
    const url = `${this.getConversationUrl(conversationId)}/zip-directory`;
    const response = await openHands.get(url, {
      responseType: "blob",
      headers: this.getConversationHeaders(),
    });
    return response.data;
  }

  /**
   * Get the web hosts
   * @returns Array of web hosts
   */
  static async getWebHosts(conversationId: string): Promise<string[]> {
    const url = `${this.getConversationUrl(conversationId)}/web-hosts`;
    const response = await openHands.get(url, {
      headers: this.getConversationHeaders(),
    });
    return Object.keys(response.data.hosts);
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
    const url = `${this.getConversationUrl(conversationId)}/vscode-url`;
    const { data } = await openHands.get<GetVSCodeUrlResponse>(url, {
      headers: this.getConversationHeaders(),
    });
    return data;
  }

  static async getRuntimeId(
    conversationId: string,
  ): Promise<{ runtime_id: string }> {
    const url = `${this.getConversationUrl(conversationId)}/config`;
    const { data } = await openHands.get<{ runtime_id: string }>(url, {
      headers: this.getConversationHeaders(),
    });
    return data;
  }

  static async getUserConversations(): Promise<Conversation[]> {
    const { data } = await openHands.get<ResultSet<Conversation>>(
      "/api/conversations?limit=100",
    );
    return data.results;
  }

  static async searchConversations(
    selectedRepository?: string,
    conversationTrigger?: string,
    limit: number = 20,
  ): Promise<Conversation[]> {
    const params = new URLSearchParams();
    params.append("limit", limit.toString());

    if (selectedRepository) {
      params.append("selected_repository", selectedRepository);
    }

    if (conversationTrigger) {
      params.append("conversation_trigger", conversationTrigger);
    }

    const { data } = await openHands.get<ResultSet<Conversation>>(
      `/api/conversations?${params.toString()}`,
    );
    return data.results;
  }

  static async deleteUserConversation(conversationId: string): Promise<boolean> {
    try {
      await openHands.delete(`/api/conversations/${conversationId}`);
      if (this.currentConversation?.conversation_id === conversationId) {
        this.setCurrentConversation(null);
      }
      return true;
    } catch (err) {
      // Treat not found or other errors as a failed delete without throwing to the UI layer
      return false;
    }
  }

  static async createConversation(
    selectedRepository?: string,
    git_provider?: Provider,
    initialUserMsg?: string,
    suggested_task?: SuggestedTask,
    selected_branch?: string,
    conversationInstructions?: string,
    createMicroagent?: CreateMicroagent,
  ): Promise<Conversation> {
    const body = {
      repository: selectedRepository,
      git_provider,
      selected_branch,
      initial_user_msg: initialUserMsg,
      suggested_task,
      conversation_instructions: conversationInstructions,
      create_microagent: createMicroagent,
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

  static async startConversation(
    conversationId: string,
    providers?: Provider[],
  ): Promise<Conversation | null> {
    const { data } = await openHands.post<Conversation | null>(
      `/api/conversations/${conversationId}/start`,
      providers ? { providers_set: providers } : {},
    );

    return data;
  }

  static async stopConversation(
    conversationId: string,
  ): Promise<Conversation | null> {
    const { data } = await openHands.post<Conversation | null>(
      `/api/conversations/${conversationId}/stop`,
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
    selected_provider?: Provider,
  ): Promise<GitRepository[]> {
    const response = await openHands.get<GitRepository[]>(
      "/api/user/search/repositories",
      {
        params: {
          query,
          per_page,
          selected_provider,
        },
      },
    );

    return response.data;
  }

  static async getTrajectory(
    conversationId: string,
  ): Promise<GetTrajectoryResponse> {
    const url = `${this.getConversationUrl(conversationId)}/trajectory`;
    const { data } = await openHands.get<GetTrajectoryResponse>(url, {
      headers: this.getConversationHeaders(),
    });
    return data;
  }

  static async logout(appMode: GetConfigResponse["APP_MODE"]): Promise<void> {
    const endpoint =
      appMode === "saas" ? "/api/logout" : "/api/unset-provider-tokens";
    await openHands.post(endpoint);
  }

  static async getGitChanges(conversationId: string): Promise<GitChange[]> {
    const url = `${this.getConversationUrl(conversationId)}/git/changes`;
    const { data } = await openHands.get<GitChange[]>(url, {
      headers: this.getConversationHeaders(),
    });
    return data;
  }

  static async getGitChangeDiff(
    conversationId: string,
    path: string,
  ): Promise<GitChangeDiff> {
    const url = `${this.getConversationUrl(conversationId)}/git/diff`;
    const { data } = await openHands.get<GitChangeDiff>(url, {
      params: { path },
      headers: this.getConversationHeaders(),
    });
    return data;
  }

  /**
   * @returns A list of repositories
   */
  static async retrieveUserGitRepositories(
    selected_provider: Provider,
    page = 1,
    per_page = 30,
  ) {
    const { data } = await openHands.get<GitRepository[]>(
      "/api/user/repositories",
      {
        params: {
          selected_provider,
          sort: "pushed",
          page,
          per_page,
        },
      },
    );

    const link =
      data.length > 0 && data[0].link_header ? data[0].link_header : "";
    const nextPage = extractNextPageFromLink(link);

    return { data, nextPage };
  }

  static async retrieveInstallationRepositories(
    selected_provider: Provider,
    installationIndex: number,
    installations: string[],
    page = 1,
    per_page = 30,
  ) {
    const installationId = installations[installationIndex];
    const response = await openHands.get<GitRepository[]>(
      "/api/user/repositories",
      {
        params: {
          selected_provider,
          sort: "pushed",
          page,
          per_page,
          installation_id: installationId,
        },
      },
    );
    const link =
      response.data.length > 0 && response.data[0].link_header
        ? response.data[0].link_header
        : "";
    const nextPage = extractNextPageFromLink(link);
    let nextInstallation: number | null;
    if (nextPage) {
      nextInstallation = installationIndex;
    } else if (installationIndex + 1 < installations.length) {
      nextInstallation = installationIndex + 1;
    } else {
      nextInstallation = null;
    }
    return {
      data: response.data,
      nextPage,
      installationIndex: nextInstallation,
    };
  }

  static async getRepositoryBranches(repository: string): Promise<Branch[]> {
    const { data } = await openHands.get<Branch[]>(
      `/api/user/repository/branches?repository=${encodeURIComponent(repository)}`,
    );

    return data;
  }

  /** Repo workspace endpoints */
  static async openRepo(
    conversationId: string,
    repository?: string,
    branch?: string,
  ): Promise<{ workspace_dir: string } | { error: string }> {
    const url = `${this.getConversationUrl(conversationId)}/repos/open`;
    const { data } = await openHands.post(url, { repository, branch });
    return data;
  }

  static async getRepoTree(
    conversationId: string,
    path?: string,
  ): Promise<string[]> {
    const url = `${this.getConversationUrl(conversationId)}/repos/tree`;
    const { data } = await openHands.get<string[]>(url, {
      params: { path },
    });
    return data;
  }

  static async readRepoFile(
    conversationId: string,
    path: string,
  ): Promise<{ path: string; content: string }> {
    const url = `${this.getConversationUrl(conversationId)}/repos/file`;
    const { data } = await openHands.get<{ path: string; content: string }>(
      url,
      {
        params: { path },
      },
    );
    return data;
  }

  static async writeRepoFile(
    conversationId: string,
    path: string,
    content: string,
  ): Promise<boolean> {
    const url = `${this.getConversationUrl(conversationId)}/repos/file`;
    const { status } = await openHands.put(url, { path, content });
    return status === 200;
  }

  static async sendCommand(
    conversationId: string,
    command: Record<string, unknown>,
  ): Promise<boolean> {
    const { status } = await openHands.post(`/api/options/commands`, {
      conversation_id: conversationId,
      command,
    });
    return status === 200;
  }

  static async createBranch(
    conversationId: string,
    name: string,
    from_ref?: string,
  ): Promise<boolean> {
    const url = `${this.getConversationUrl(conversationId)}/repos/branch`;
    const { status } = await openHands.post(url, { name, from_ref });
    return status === 200;
  }

  static async commitChanges(
    conversationId: string,
    message: string,
    files?: string[],
  ): Promise<boolean> {
    const url = `${this.getConversationUrl(conversationId)}/repos/commit`;
    const { status } = await openHands.post(url, { message, files });
    return status === 200;
  }

  static async createPullRequest(
    conversationId: string,
    title: string,
  ): Promise<string> {
    const url = `${this.getConversationUrl(conversationId)}/repos/pr`;
    const { data } = await openHands.post<{ url: string }>(url, { title });
    return data.url;
  }

  /**
   * Get the available microagents associated with a conversation
   * @param conversationId The ID of the conversation
   * @returns The available microagents associated with the conversation
   */
  static async getMicroagents(
    conversationId: string,
  ): Promise<GetMicroagentsResponse> {
    const url = `${this.getConversationUrl(conversationId)}/microagents`;
    const { data } = await openHands.get<GetMicroagentsResponse>(url, {
      headers: this.getConversationHeaders(),
    });
    return data;
  }

  /**
   * Get the available microagents for a repository
   * @param owner The repository owner
   * @param repo The repository name
   * @returns The available microagents for the repository
   */
  static async getRepositoryMicroagents(
    owner: string,
    repo: string,
  ): Promise<RepositoryMicroagent[]> {
    const { data } = await openHands.get<RepositoryMicroagent[]>(
      `/api/user/repository/${owner}/${repo}/microagents`,
    );
    return data;
  }

  /**
   * Get the content of a specific microagent from a repository
   * @param owner The repository owner
   * @param repo The repository name
   * @param filePath The path to the microagent file within the repository
   * @returns The microagent content and metadata
   */
  static async getRepositoryMicroagentContent(
    owner: string,
    repo: string,
    filePath: string,
  ): Promise<MicroagentContentResponse> {
    const { data } = await openHands.get<MicroagentContentResponse>(
      `/api/user/repository/${owner}/${repo}/microagents/content`,
      {
        params: { file_path: filePath },
      },
    );
    return data;
  }

  static async getMicroagentPrompt(
    conversationId: string,
    eventId: number,
  ): Promise<string> {
    const url = `${this.getConversationUrl(conversationId)}/remember-prompt`;
    const { data } = await openHands.get<GetMicroagentPromptResponse>(url, {
      params: { event_id: eventId },
      headers: this.getConversationHeaders(),
    });

    return data.prompt;
  }

  static async updateConversation(
    conversationId: string,
    updates: { title: string },
  ): Promise<boolean> {
    const { data } = await openHands.patch<boolean>(
      `/api/conversations/${conversationId}`,
      updates,
    );

    return data;
  }

  /**
   * Retrieve the list of files available in the workspace
   * @param conversationId ID of the conversation
   * @param path Path to list files from. If provided, it lists all the files in the given path
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  static async getFiles(
    conversationId: string,
    path?: string,
  ): Promise<GetFilesResponse> {
    const url = `${this.getConversationUrl(conversationId)}/list-files`;
    const { data } = await openHands.get<GetFilesResponse>(url, {
      params: { path },
      headers: this.getConversationHeaders(),
    });

    return data;
  }

  /**
   * Retrieve the content of a file
   * @param conversationId ID of the conversation
   * @param path Full path of the file to retrieve
   * @returns Code content of the file
   */
  static async getFile(conversationId: string, path: string): Promise<string> {
    const url = `${this.getConversationUrl(conversationId)}/select-file`;
    const { data } = await openHands.get<GetFileResponse>(url, {
      params: { file: path },
      headers: this.getConversationHeaders(),
    });

    return data.code;
  }

  /**
   * Upload multiple files to the workspace
   * @param conversationId ID of the conversation
   * @param files List of files.
   * @returns list of uploaded files, list of skipped files
   */
  static async uploadFiles(
    conversationId: string,
    files: File[],
  ): Promise<FileUploadSuccessResponse> {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }
    const url = `${this.getConversationUrl(conversationId)}/upload-files`;
    const response = await openHands.post<FileUploadSuccessResponse>(
      url,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
          ...this.getConversationHeaders(),
        },
      },
    );
    return response.data;
  }

  /**
   * Get the user installation IDs
   * @param provider The provider to get installation IDs for (github, bitbucket, etc.)
   * @returns List of installation IDs
   */
  static async getUserInstallationIds(provider: Provider): Promise<string[]> {
    const { data } = await openHands.get<string[]>(
      `/api/user/installations?provider=${provider}`,
    );
    return data;
  }

  static async getRepoDiff(
    conversationId: string,
    path: string,
  ): Promise<{ original: string; modified: string }> {
    const url = `${this.getConversationUrl(conversationId)}/repos/diff`;
    const { data } = await openHands.get<{
      original: string;
      modified: string;
    }>(url, { params: { path } });
    return data;
  }

  static async getRepoJobStatus(
    conversationId: string,
    jobId: string,
  ): Promise<{
    id: string;
    type: string;
    status: string;
    progress: number;
    result?: unknown;
    error?: string;
  }> {
    const url = `${this.getConversationUrl(conversationId)}/repos/jobs/${jobId}`;
    const { data } = await openHands.get<{
      id: string;
      type: string;
      status: string;
      progress: number;
      result?: unknown;
      error?: string;
    }>(url);
    return data;
  }
}

export default OpenHands;
