import { UserSettings } from "#/api/settings-service/settings-service.types";
import { DEFAULT_SETTINGS } from "#/services/settings";

export const hasAdvancedSettingsSet = (settings: UserSettings): boolean =>
  !!settings.llm_base_url ||
  settings.agent !== DEFAULT_SETTINGS.agent ||
  settings.remote_runtime_resource_factor !==
    DEFAULT_SETTINGS.remote_runtime_resource_factor ||
  settings.confirmation_mode ||
  !!settings.security_analyzer;
