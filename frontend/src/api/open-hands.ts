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
  RepoInstructions,
  MicroAgent,
  CreateInstructionsPRResponse,
  AddMicroAgentResponse,
} from "./open-hands.types";
import { openHands } from "./open-hands-axios";

class OpenHands {
  static async getModels(): Promise<string[]> {
    const { data } = await openHands.get<string[]>("/api/options/models");
    return data;
  }

  static async getAgents(): Promise<string[]> {
    const { data } = await openHands.get<string[]>("/api/options/agents");
    return data;
  }

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

  static async getFiles(path?: string): Promise<string[]> {
    const { data } = await openHands.get<string[]>("/api/list-files", {
      params: { path },
    });
    return data;
  }

  static async getFile(path: string): Promise<string> {
    const { data } = await openHands.get<{ code: string }>("/api/select-file", {
      params: { file: path },
    });

    return data.code;
  }

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

  static async uploadFiles(files: File[]): Promise<FileUploadSuccessResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const { data } = await openHands.post<
      FileUploadSuccessResponse | ErrorResponse
    >("/api/upload-files", formData);

    if ("error" in data) throw new Error(data.error);
    return data;
  }

  static async submitFeedback(feedback: Feedback): Promise<FeedbackResponse> {
    const { data } = await openHands.post<FeedbackResponse>(
      "/api/submit-feedback",
      feedback,
    );
    return data;
  }

  static async authenticate(
    appMode: GetConfigResponse["APP_MODE"],
  ): Promise<boolean> {
    if (appMode === "oss") return true;

    const response =
      await openHands.post<AuthenticateResponse>("/api/authenticate");
    return response.status === 200;
  }

  static async getWorkspaceZip(): Promise<Blob> {
    const response = await openHands.get("/api/zip-directory", {
      responseType: "blob",
    });
    return response.data;
  }

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

  static async getRepoInstructions(repoName: string): Promise<RepoInstructions> {
    const { data } = await openHands.get<RepoInstructions>("/api/instructions", {
      params: { repo: repoName },
    });
    return data;
  }

  static async createInstructionsPR(
    repoName: string,
    instructions: string,
  ): Promise<CreateInstructionsPRResponse> {
    const { data } = await openHands.post<CreateInstructionsPRResponse>(
      "/api/instructions/create",
      {
        repo: repoName,
        instructions,
      },
    );
    return data;
  }

  static async getMicroAgents(repoName: string): Promise<MicroAgent[]> {
    const { data } = await openHands.get<MicroAgent[]>("/api/microagents", {
      params: { repo: repoName },
    });
    return data;
  }

  static async addTemporaryMicroAgent(
    repoName: string,
    instructions: string,
  ): Promise<AddMicroAgentResponse> {
    const { data } = await openHands.post<AddMicroAgentResponse>(
      "/api/microagents/temporary",
      {
        repo: repoName,
        instructions,
      },
    );
    return data;
  }

  static async addPermanentMicroAgent(
    repoName: string,
    instructions: string,
  ): Promise<AddMicroAgentResponse> {
    const { data } = await openHands.post<AddMicroAgentResponse>(
      "/api/microagents/permanent",
      {
        repo: repoName,
        instructions,
      },
    );
    return data;
  }
}

export default OpenHands;
