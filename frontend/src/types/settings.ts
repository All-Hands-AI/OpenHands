export const ProviderOptions = {
  github: "github",
  gitlab: "gitlab",
} as const;

export type Provider = keyof typeof ProviderOptions;

export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY_SET: boolean;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
  REMOTE_RUNTIME_RESOURCE_FACTOR: number | null;
  PROVIDER_TOKENS_SET: Record<Provider, boolean>;
  ENABLE_DEFAULT_CONDENSER: boolean;
  ENABLE_SOUND_NOTIFICATIONS: boolean;
  USER_CONSENTS_TO_ANALYTICS: boolean | null;
  PROVIDER_TOKENS: Record<Provider, string>;
  IS_NEW_USER?: boolean;
};

export type ApiSettings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  llm_api_key_set: boolean;
  confirmation_mode: boolean;
  security_analyzer: string;
  remote_runtime_resource_factor: number | null;
  enable_default_condenser: boolean;
  enable_sound_notifications: boolean;
  user_consents_to_analytics: boolean | null;
  provider_tokens: Record<Provider, string>;
  provider_tokens_set: Record<Provider, boolean>;
};

export type PostSettings = Settings & {
  provider_tokens: Record<Provider, string>;
  user_consents_to_analytics: boolean | null;
  llm_api_key?: string | null;
};

export type PostApiSettings = ApiSettings & {
  provider_tokens: Record<Provider, string>;
  user_consents_to_analytics: boolean | null;
};
