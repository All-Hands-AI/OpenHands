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
    const { data } = await openHands.get<GetConfigResponse>("/config.json");
    return data;
  }

  /**
   * Retrieve the list of files available in the workspace
   * @param path Path to list files from
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  static async getFiles(path?: string): Promise<string[]> {
    const { data } = await openHands.get<string[]>("/api/list-files", {
      params: { path },
    });
    return data;
  }

  /**
   * Retrieve the content of a file
   * @param path Full path of the file to retrieve
   * @returns Content of the file
   */
  static async getFile(path: string): Promise<string> {
    const { data } = await openHands.get<{ code: string }>("/api/select-file", {
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
    path: string,
    content: string,
  ): Promise<SaveFileSuccessResponse> {
    const { data } = await openHands.post<
      SaveFileSuccessResponse | ErrorResponse
    >("/api/save-file", {
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
  static async uploadFiles(files: File[]): Promise<FileUploadSuccessResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const { data } = await openHands.post<
      FileUploadSuccessResponse | ErrorResponse
    >("/api/upload-files", formData);

    if ("error" in data) throw new Error(data.error);
    return data;
  }

  /**
   * Send feedback to the server
   * @param data Feedback data
   * @returns The stored feedback data
   */
  static async submitFeedback(feedback: Feedback): Promise<FeedbackResponse> {
    const { data } = await openHands.post<FeedbackResponse>(
      "/api/submit-feedback",
      feedback,
    );
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
   * Get the blob of the workspace zip
   * @returns Blob of the workspace zip
   */
  static async getWorkspaceZip(): Promise<Blob> {
    const response = await openHands.get("/api/zip-directory", {
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
  static async getVSCodeUrl(): Promise<GetVSCodeUrlResponse> {
    const { data } =
      await openHands.get<GetVSCodeUrlResponse>("/api/vscode-url");
    return data;
  }

  static async getRuntimeId(): Promise<{ runtime_id: string }> {
    const { data } = await openHands.get<{ runtime_id: string }>(
      "/api/conversation",
    );
    return data;
  }
}

export default OpenHands;
