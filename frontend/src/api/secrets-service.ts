import { openHands } from "./open-hands-axios";
import {
  CustomSecret,
  GetSecretsResponse,
  POSTProviderTokens,
} from "./secrets-service.types";
import { Provider, ProviderToken } from "#/types/settings";

export class SecretsService {
  static async getSecrets() {
    const { data } = await openHands.get<GetSecretsResponse>("/api/secrets");
    return data.custom_secrets;
  }

  static async createSecret(name: string, value: string) {
    const secret: CustomSecret = {
      name,
      value,
    };

    const { data } = await openHands.post<boolean>("/api/secrets", secret);
    return data;
  }

  static async updateSecret(id: string, name: string, value: string) {
    const secret: CustomSecret = {
      name,
      value,
    };

    const { data } = await openHands.put<boolean>(`/api/secrets/${id}`, secret);
    return data;
  }

  static async deleteSecret(id: string) {
    const { data } = await openHands.delete<boolean>(`/api/secrets/${id}`);
    return data;
  }

  static async addGitProvider(providers: Record<Provider, ProviderToken>) {
    const tokens: POSTProviderTokens = {
      provider_tokens: providers,
    };
    const { data } = await openHands.post<boolean>(
      "/api/add-git-providers",
      tokens,
    );
    return data;
  }
}
