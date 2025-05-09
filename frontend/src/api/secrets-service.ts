import { Provider, ProviderToken } from "#/types/settings";
import { openHands } from "./open-hands-axios";
import { POSTProviderTokens } from "./secrets-service.types";

export class SecretsService {
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
