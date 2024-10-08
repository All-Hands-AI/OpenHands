interface ErrorResponse {
  error: string;
}

interface SaveFileSuccessResponse {
  message: string;
}

interface FileUploadSuccessResponse {
  message: string;
  uploaded_files: string[];
  skipped_files: { name: string; reason: string }[];
}

interface FeedbackBodyResponse {
  message: string;
  feedback_id: string;
  password: string;
}

interface FeedbackResponse {
  statusCode: number;
  body: FeedbackBodyResponse;
}

export interface Feedback {
  version: string;
  email: string;
  token: string;
  feedback: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}

/**
 * Class to interact with the OpenHands API
 */
class OpenHands {
  /**
   * Base URL of the OpenHands API
   */
  static BASE_URL = "http://localhost:3000";

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
   * @returns List of files available in the workspace
   */
  static async getFiles(token: string): Promise<string[]> {
    const response = await fetch(`${OpenHands.BASE_URL}/api/list-files`, {
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
  static async uploadFile(
    token: string,
    file: File,
  ): Promise<FileUploadSuccessResponse | ErrorResponse> {
    const formData = new FormData();
    formData.append("files", file);

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
