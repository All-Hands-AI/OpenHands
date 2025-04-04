import { openHands } from "./open-hands-axios";

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface CreateApiKeyResponse {
  id: string;
  name: string;
  key: string; // Full key, only returned once upon creation
  prefix: string;
  created_at: string;
}

class ApiKeysClient {
  /**
   * Get all API keys for the current user
   */
  static async getApiKeys(): Promise<ApiKey[]> {
    const { data } = await openHands.get<ApiKey[]>("/api/api-keys");
    return data;
  }

  /**
   * Create a new API key
   * @param name - A descriptive name for the API key
   */
  static async createApiKey(name: string): Promise<CreateApiKeyResponse> {
    const { data } = await openHands.post<CreateApiKeyResponse>(
      "/api/api-keys",
      {
        name,
      },
    );
    return data;
  }

  /**
   * Delete an API key
   * @param id - The ID of the API key to delete
   */
  static async deleteApiKey(id: string): Promise<void> {
    await openHands.delete(`/api/api-keys/${id}`);
  }
}

export default ApiKeysClient;
