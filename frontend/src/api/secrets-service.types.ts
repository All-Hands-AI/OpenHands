import { Provider, ProviderToken } from "#/types/settings";

export type CustomSecret = {
  name: string;
  value: string;
  description?: string;
};

export interface GetSecretsResponse {
  custom_secrets: Omit<CustomSecret, "value">[];
}

export interface POSTProviderTokens {
  provider_tokens: Record<Provider, ProviderToken>;
}
