import { DEFAULT_SETTINGS } from "#/services/settings";
import { Settings } from "#/types/settings";

export const hasAdvancedSettingsSet = (settings: Partial<Settings>): boolean =>
  !!settings.LLM_BASE_URL ||
  settings.AGENT !== DEFAULT_SETTINGS.AGENT ||
  settings.REMOTE_RUNTIME_RESOURCE_FACTOR !==
    DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR ||
  settings.CONFIRMATION_MODE ||
  !!settings.SECURITY_ANALYZER;
