import { request } from "#/services/api";
import {
  SaveFileSuccessResponse,
  FileUploadSuccessResponse,
  Feedback,
  FeedbackResponse,
  GitHubAccessTokenResponse,
  ErrorResponse,
  GetConfigResponse,
  GetVSCodeUrlResponse,
} from "./open-hands.types";

class OpenHands {
  /**
   * Retrieve the list of models available
   * @returns List of models available
   */
  static async getModels(): Promise<string[]> {
    const response = await fetch("/api/options/models");

    if (!response.ok) {
      throw new Error("Failed to fetch models");
    }

    return response.json();
  }

  /**
   * Retrieve the list of agents available
   * @returns List of agents available
   */
  static async getAgents(): Promise<string[]> {
    const response = await fetch("/api/options/agents");

    if (!response.ok) {
      throw new Error("Failed to fetch agents");
    }

    return response.json();
  }

  /**
   * Retrieve the list of security analyzers available
   * @returns List of security analyzers available
   */
  static async getSecurityAnalyzers(): Promise<string[]> {
    const response = await fetch("/api/options/security-analyzers");

    if (!response.ok) {
      throw new Error("Failed to fetch security analyzers");
    }

    return response.json();
  }

  static async getConfig(): Promise<GetConfigResponse> {
    const response = await fetch("/config.json");

    if (!response.ok) {
      throw new Error("Failed to fetch config");
    }

    return response.json();
  }

  /**
   * Retrieve the list of files available in the workspace
   * @param path Path to list files from
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  static async getFiles(token: string, path?: string): Promise<string[]> {
    const url = new URL("/api/list-files", window.location.origin);
    if (path) url.searchParams.append("path", path);

    const response = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch files");
    }

    return response.json();
  }

  /**
   * Retrieve the content of a file
   * @param path Full path of the file to retrieve
   * @returns Content of the file
   */
  static async getFile(token: string, path: string): Promise<string> {
    const url = new URL("/api/select-file", window.location.origin);
    url.searchParams.append("file", path);

    const response = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch file");
    }

    const data = await response.json();
    return data.code;
  }

  /**
   * Save the content of a file
   * @param path Full path of the file to save
   * @param content Content to save in the file
   * @returns Success message or error message
   */
  static async saveFile(
    token: string,
    path: string,
    content: string,
  ): Promise<SaveFileSuccessResponse> {
    const response = await fetch("/api/save-file", {
      method: "POST",
      body: JSON.stringify({ filePath: path, content }),
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to save file");
    }

    const data = (await response.json()) as
      | SaveFileSuccessResponse
      | ErrorResponse;

    if ("error" in data) {
      throw new Error(data.error);
    }

    return data;
  }

  /**
   * Upload a file to the workspace
   * @param file File to upload
   * @returns Success message or error message
   */
  static async uploadFiles(
    token: string,
    files: File[],
  ): Promise<FileUploadSuccessResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const response = await fetch("/api/upload-files", {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to upload files");
    }

    const data = (await response.json()) as
      | FileUploadSuccessResponse
      | ErrorResponse;

    if ("error" in data) {
      throw new Error(data.error);
    }

    return data;
  }

  /**
   * Send feedback to the server
   * @param data Feedback data
   * @returns The stored feedback data
   */
  static async submitFeedback(
    token: string,
    feedback: Feedback,
  ): Promise<FeedbackResponse> {
    const response = await fetch("/api/submit-feedback", {
      method: "POST",
      body: JSON.stringify(feedback),
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to submit feedback");
    }

    return response.json();
  }

  /**
   * Authenticate with GitHub token
   * @returns Response with authentication status and user info if successful
   */
  static async authenticate(
    gitHubToken: string,
    appMode: GetConfigResponse["APP_MODE"],
  ): Promise<boolean> {
    if (appMode === "oss") return true;

    const response = await fetch("/api/authenticate", {
      method: "POST",
      headers: {
        "X-GitHub-Token": gitHubToken,
      },
    });

    return response.ok;
  }

  /**
   * Get the blob of the workspace zip
   * @returns Blob of the workspace zip
   */
  static async getWorkspaceZip(): Promise<Blob> {
    const response = await request(`/api/zip-directory`, {}, false, true);
    return response.blob();
  }

  /**
   * @param code Code provided by GitHub
   * @returns GitHub access token
   */
  static async getGitHubAccessToken(
    code: string,
  ): Promise<GitHubAccessTokenResponse> {
    const response = await fetch("/api/github/callback", {
      method: "POST",
      body: JSON.stringify({ code }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to get GitHub access token");
    }

    return response.json();
  }

  /**
   * Get the VSCode URL
   * @returns VSCode URL
   */
  static async getVSCodeUrl(): Promise<GetVSCodeUrlResponse> {
    return request(`/api/vscode-url`, {}, false, false, 1);
  }

  static async getRuntimeId(): Promise<{ runtime_id: string }> {
    const data = await request("/api/conversation");

    return data;
  }
}

export default OpenHands;
