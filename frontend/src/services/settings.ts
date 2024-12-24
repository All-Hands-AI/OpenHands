import OpenHands from "#/api/open-hands";
import { Settings } from "#/api/open-hands.types";

export const LATEST_SETTINGS_VERSION = 4;

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  MAX_ITERATIONS: 100,
  LANGUAGE: "en",
  LLM_API_KEY: "",
  CONFIRMATION_MODE: false,
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

export const maybeMigrateSettings = (logout: () => void) => {
  // Sometimes we ship major changes, like a new default agent.
  // In this case, we may want to override a previous choice made by the user.
  const currentVersion = getCurrentSettingsVersion();

  if (currentVersion < 1) {
    // localStorage.setItem("AGENT", DEFAULT_SETTINGS.AGENT);
  }
  if (currentVersion < 2) {
    const customModel = localStorage.getItem("CUSTOM_LLM_MODEL");
    if (customModel) {
      localStorage.setItem("LLM_MODEL", customModel);
    }
    localStorage.removeItem("CUSTOM_LLM_MODEL");
    localStorage.removeItem("USING_CUSTOM_MODEL");
  }
  if (currentVersion < 3) {
    localStorage.removeItem("token");
  }

  if (currentVersion < 4) {
    logout();
  }
};
