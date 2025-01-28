export const LATEST_SETTINGS_VERSION = 5;

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
};

export type PostSettings = Settings & {
  github_token: string;
  unset_github_token: boolean;
};

export type PostApiSettings = ApiSettings & {
  github_token: string;
  unset_github_token: boolean;
};

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: null,
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
  REMOTE_RUNTIME_RESOURCE_FACTOR: 1,
  GITHUB_TOKEN_IS_SET: false,
  ENABLE_DEFAULT_CONDENSER: false,
};

export const getCurrentSettingsVersion = () => {
  const settingsVersion = localStorage.getItem("SETTINGS_VERSION");
  if (!settingsVersion) return 0;
  try {
    return parseInt(settingsVersion, 10);
  } catch (e) {
    return 0;
  }
};

export const settingsAreUpToDate = () =>
  getCurrentSettingsVersion() === LATEST_SETTINGS_VERSION;

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;
