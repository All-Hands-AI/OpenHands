export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string | null;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
  REMOTE_RUNTIME_RESOURCE_FACTOR: number;
  GITHUB_TOKEN_IS_SET: boolean;
  ENABLE_DEFAULT_CONDENSER: boolean;
  USER_CONSENTS_TO_ANALYTICS: boolean | null;
};

export type ApiSettings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  confirmation_mode: boolean;
  security_analyzer: string;
  remote_runtime_resource_factor: number;
  github_token_is_set: boolean;
  enable_default_condenser: boolean;
  user_consents_to_analytics: boolean | null;
};

export type PostSettings = Settings & {
  github_token: string;
  unset_github_token: boolean;
  user_consents_to_analytics: boolean | null;
};

export type PostApiSettings = ApiSettings & {
  github_token: string;
  unset_github_token: boolean;
  user_consents_to_analytics: boolean | null;
};
