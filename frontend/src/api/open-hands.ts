import { getValidFallbackHost } from "#/utils/get-valid-fallback-host";
import {
  SaveFileSuccessResponse,
  FileUploadSuccessResponse,
  Feedback,
  FeedbackResponse,
  GitHubAccessTokenResponse,
  ErrorResponse,
} from "./open-hands.types";

/**
 * Generate the base URL of the OpenHands API
 * @returns Base URL of the OpenHands API
 */
const generateBaseURL = () => {
  const fallback = getValidFallbackHost();
  const baseUrl = import.meta.env.VITE_BACKEND_BASE_URL || fallback;

  if (typeof window === "undefined") {
    return `http://${baseUrl}`;
  }
  return `${window.location.protocol}//${baseUrl}`;
};

/**
 * Class to interact with the OpenHands API
 */
class OpenHands {
  /**
   * Base URL of the OpenHands API
   */
  static BASE_URL = generateBaseURL();

  /**
   * Retrieve the list of models available
   * @returns List of models available
   */
  static async getModels(): Promise<string[]> {
    const response = await fetch(`${OpenHands.BASE_URL}/api/options/models`);
    return response.json();
  }

  /**
   * Retrieve the list of agents available
   * @returns List of agents available
   */
  static async getAgents(): Promise<string[]> {
    const response = await fetch(`${OpenHands.BASE_URL}/api/options/agents`);
    return response.json();
  }

  /**
   * Retrieve the list of security analyzers available
   * @returns List of security analyzers available
   */
  static async getSecurityAnalyzers(): Promise<string[]> {
    const response = await fetch(
      `${OpenHands.BASE_URL}/api/options/security-analyzers`,
    );
    return response.json();
  }

  /**
   * Retrieve the list of files available in the workspace
   * @param token User token provided by the server
   * @param path Path to list files from
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  static async getFiles(token: string, path?: string): Promise<string[]> {
    const url = new URL(`${OpenHands.BASE_URL}/api/list-files`);
    if (path) url.searchParams.append("path", path);

    const response = await fetch(url.toString(), {
      headers: OpenHands.generateHeaders(token),
    });

    return response.json();
  }

  /**
   * Retrieve the content of a file
   * @param token User token provided by the server
   * @param path Full path of the file to retrieve
   * @returns Content of the file
   */
  static async getFile(token: string, path: string): Promise<string> {
    const url = new URL(`${OpenHands.BASE_URL}/api/select-file`);
    url.searchParams.append("file", path);
    const response = await fetch(url.toString(), {
      headers: OpenHands.generateHeaders(token),
    });

    const data = await response.json();
    return data.code;
  }

  /**
   * Save the content of a file
   * @param token User token provided by the server
   * @param path Full path of the file to save
   * @param content Content to save in the file
   * @returns Success message or error message
   */
  static async saveFile(
    token: string,
    path: string,
    content: string,
  ): Promise<SaveFileSuccessResponse | ErrorResponse> {
    const response = await fetch(`${OpenHands.BASE_URL}/api/save-file`, {
      method: "POST",
      body: JSON.stringify({ filePath: path, content }),
      headers: OpenHands.generateHeaders(token),
    });

    return response.json();
  }

  /**
   * Upload a file to the workspace
   * @param token User token provided by the server
   * @param file File to upload
   * @returns Success message or error message
   */
  static async uploadFiles(
    token: string,
    file: File[],
  ): Promise<FileUploadSuccessResponse | ErrorResponse> {
    const formData = new FormData();
    file.forEach((f) => formData.append("files", f));

    const response = await fetch(`${OpenHands.BASE_URL}/api/upload-files`, {
      method: "POST",
      headers: OpenHands.generateHeaders(token),
      body: formData,
    });

    return response.json();
  }

  /**
   * Get the blob of the workspace zip
   * @param token User token provided by the server
   * @returns Blob of the workspace zip
   */
  static async getWorkspaceZip(token: string): Promise<Blob> {
    const response = await fetch(`${OpenHands.BASE_URL}/api/zip-directory`, {
      headers: OpenHands.generateHeaders(token),
    });
    return response.blob();
  }

  /**
   * Send feedback to the server
   * @param token User token provided by the server
   * @param data Feedback data
   * @returns The stored feedback data
   */
  static async sendFeedback(
    token: string,
    data: Feedback,
    // TODO: Type the response
  ): Promise<FeedbackResponse> {
    const response = await fetch(`${OpenHands.BASE_URL}/api/submit-feedback`, {
      method: "POST",
      headers: OpenHands.generateHeaders(token),
      body: JSON.stringify(data),
    });

    return response.json();
  }

  /**
   * Get the GitHub access token
   * @param code Code provided by GitHub
   * @returns GitHub access token
   */
  static async getGitHubAccessToken(
    code: string,
  ): Promise<GitHubAccessTokenResponse> {
    const response = await fetch(`${OpenHands.BASE_URL}/github/callback`, {
      method: "POST",
      body: JSON.stringify({ code }),
    });

    return response.json();
  }

  /**
   * Generate the headers for the request
   * @param token User token provided by the server
   * @returns Headers for the request
   */
  private static generateHeaders(token: string) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
}

export default OpenHands;
