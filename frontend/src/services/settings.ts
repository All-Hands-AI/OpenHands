import { Settings } from "#/types/settings";

export const LATEST_SETTINGS_VERSION = 5;

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY_SET: false,
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
  REMOTE_RUNTIME_RESOURCE_FACTOR: 1,
  PROVIDER_TOKENS_SET: { github: false, gitlab: false },
  ENABLE_DEFAULT_CONDENSER: true,
  ENABLE_SOUND_NOTIFICATIONS: false,
  USER_CONSENTS_TO_ANALYTICS: false,
  PROVIDER_TOKENS: {
    github: "",
    gitlab: "",
  },
  IS_NEW_USER: true,
};

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;
