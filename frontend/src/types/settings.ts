export const ProviderOptions = {
  github: "github",
  gitlab: "gitlab",
} as const;

export type Provider = keyof typeof ProviderOptions;

// For GET requests (data received from backend)
export type ProviderTokenDataGet = {
  host_url?: string;
};

// For POST requests (data sent to backend)
export type ProviderTokenDataPost = {
  token: string;
  host_url?: string;
};

// Kept for backward compatibility
export type ProviderTokenData = ProviderTokenDataPost;

export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string | null;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
  REMOTE_RUNTIME_RESOURCE_FACTOR: number | null;
  PROVIDER_TOKENS_SET: Record<Provider, boolean>;
  ENABLE_DEFAULT_CONDENSER: boolean;
  ENABLE_SOUND_NOTIFICATIONS: boolean;
  USER_CONSENTS_TO_ANALYTICS: boolean | null;
  PROVIDER_TOKENS: Record<Provider, ProviderTokenDataGet | string>;
  IS_NEW_USER?: boolean;
};

export type ApiSettings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  confirmation_mode: boolean;
  security_analyzer: string;
  remote_runtime_resource_factor: number | null;
  enable_default_condenser: boolean;
  enable_sound_notifications: boolean;
  user_consents_to_analytics: boolean | null;
  provider_tokens: Record<Provider, ProviderTokenDataGet | string>;
  provider_tokens_set: Record<Provider, boolean>;
};

export type PostSettings = Settings & {
  provider_tokens: Record<Provider, ProviderTokenDataPost | string>;
  user_consents_to_analytics: boolean | null;
};

export type PostApiSettings = ApiSettings & {
  provider_tokens: Record<Provider, ProviderTokenDataPost | string>;
  user_consents_to_analytics: boolean | null;
};
