import { Provider, ProviderToken } from "#/types/settings";

export interface POSTProviderTokens {
  provider_tokens: Record<Provider, ProviderToken>;
}
