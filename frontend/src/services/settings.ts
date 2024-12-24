import OpenHands from "#/api/open-hands";
import { Settings } from "#/api/open-hands.types";

export const LATEST_SETTINGS_VERSION = 4;

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: "",
  CONFIRMATION_MODEL: false,
  SECURITY_ANALYZER: "",
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

/**
 * Get the settings from the backend or use the default settings if not found
 */
export const getSettings = async (): Promise<Settings> => {
  const settings = await OpenHands.loadSettings();
  return settings || DEFAULT_SETTINGS;
};

/**
 * Save the settings to the backend
 * @param settings - the settings to save
 */
export const saveSettings = async (
  settings: Partial<Settings>,
): Promise<void> => {
  const currentSettings = await getSettings();
  const newSettings = {
    ...currentSettings,
    ...settings,
  };
  await OpenHands.storeSettings(newSettings);
};
