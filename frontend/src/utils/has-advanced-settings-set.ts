import { DEFAULT_SETTINGS } from "#/services/settings";
import { ApiSettings } from "#/types/settings";

export const hasAdvancedSettingsSet = (settings: ApiSettings): boolean =>
  !!settings.llm_base_url ||
  settings.agent !== DEFAULT_SETTINGS.AGENT ||
  settings.remote_runtime_resource_factor !==
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR ||
  !!settings.security_analyzer;
