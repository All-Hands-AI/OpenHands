import axios from "axios";
import { buildHttpBaseUrl } from "#/utils/websocket-url";
import { buildSessionHeaders } from "#/utils/utils";
import type { GitChange, GitChangeDiff } from "../open-hands.types";

class V1GitService {
  /**
   * Build the full URL for V1 runtime-specific endpoints
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param path The API path (e.g., "/api/git/changes")
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
   * Get git changes for a V1 conversation
   * Uses the agent server endpoint: GET /api/git/changes/{path}
   *
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param sessionApiKey Session API key for authentication (required for V1)
   * @param path The git repository path (e.g., /workspace/project or /workspace/project/OpenHands)
   * @returns List of git changes
   */
  static async getGitChanges(
    conversationUrl: string | null | undefined,
    sessionApiKey: string | null | undefined,
    path: string,
  ): Promise<GitChange[]> {
    const encodedPath = encodeURIComponent(path);
    const url = this.buildRuntimeUrl(
      conversationUrl,
      `/api/git/changes/${encodedPath}`,
    );
    const headers = buildSessionHeaders(sessionApiKey);

    const { data } = await axios.get<GitChange[]>(url, { headers });
    return data;
  }

  /**
   * Get git change diff for a specific file in a V1 conversation
   * Uses the agent server endpoint: GET /api/git/diff/{path}
   *
   * @param conversationUrl The conversation URL (e.g., "http://localhost:54928/api/conversations/...")
   * @param sessionApiKey Session API key for authentication (required for V1)
   * @param path The file path to get diff for
   * @returns Git change diff
   */
  static async getGitChangeDiff(
    conversationUrl: string | null | undefined,
    sessionApiKey: string | null | undefined,
    path: string,
  ): Promise<GitChangeDiff> {
    const encodedPath = encodeURIComponent(path);
    const url = this.buildRuntimeUrl(
      conversationUrl,
      `/api/git/diff/${encodedPath}`,
    );
    const headers = buildSessionHeaders(sessionApiKey);

    const { data } = await axios.get<GitChangeDiff>(url, { headers });
    return data;
  }
}

export default V1GitService;
