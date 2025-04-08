import { ClientUserSettings } from "#/api/settings-service/settings-service.types";

export const LATEST_SETTINGS_VERSION = 5;

export const DEFAULT_SETTINGS: ClientUserSettings = {
  llm_model: "anthropic/claude-3-5-sonnet-20241022",
  llm_base_url: "",
  agent: "CodeActAgent",
  language: "en",
  llm_api_key_set: null,
  confirmation_mode: false,
  security_analyzer: "",
  remote_runtime_resource_factor: 1,
  github_token_is_set: false,
  enable_default_condenser: true,
  enable_sound_notifications: false,
  user_consents_to_analytics: false,
  provider_tokens_set: {
    github: false,
    gitlab: false,
  },
  is_new_user: true,
};

/**
 * Get the default settings
 */
export const getDefaultSettings = () => DEFAULT_SETTINGS;
