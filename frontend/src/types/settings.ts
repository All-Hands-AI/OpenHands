export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string | null;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
  REMOTE_RUNTIME_RESOURCE_FACTOR: number | null;
  TOKEN_IS_SET: boolean;
  TOKEN_TYPE: 'github' | 'gitlab' | null;
  ENABLE_DEFAULT_CONDENSER: boolean;
  ENABLE_SOUND_NOTIFICATIONS: boolean;
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
  remote_runtime_resource_factor: number | null;
  token_is_set: boolean;
  token_type: 'github' | 'gitlab' | null;
  enable_default_condenser: boolean;
  enable_sound_notifications: boolean;
  user_consents_to_analytics: boolean | null;
};

export type PostSettings = Settings & {
  token: string;
  token_type: 'github' | 'gitlab' | null;
  unset_token: boolean;
  user_consents_to_analytics: boolean | null;
};

export type PostApiSettings = ApiSettings & {
  token: string;
  token_type: 'github' | 'gitlab' | null;
  unset_token: boolean;
  user_consents_to_analytics: boolean | null;
};
