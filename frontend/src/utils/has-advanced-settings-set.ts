import { DEFAULT_SETTINGS } from "#/services/settings";
import { Settings } from "#/types/settings";

export const hasAdvancedSettingsSet = (settings: Partial<Settings>): boolean =>
  Object.keys(settings).length > 0 &&
  (!!settings.LLM_BASE_URL ||
    settings.AGENT !== DEFAULT_SETTINGS.AGENT);
