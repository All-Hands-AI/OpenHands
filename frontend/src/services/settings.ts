const LATEST_SETTINGS_VERSION = 1;

export type Settings = {
  LLM_MODEL: string;
  CUSTOM_LLM_MODEL: string;
  USING_CUSTOM_MODEL: boolean;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
};

type SettingsInput = Settings[keyof Settings];

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "openai/gpt-4o",
  CUSTOM_LLM_MODEL: "",
  USING_CUSTOM_MODEL: false,
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: "",
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
};

const validKeys = Object.keys(DEFAULT_SETTINGS) as (keyof Settings)[];

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

export const maybeMigrateSettings = () => {
  // Sometimes we ship major changes, like a new default agent.
  // In this case, we may want to override a previous choice made by the user.
  const currentVersion = getCurrentSettingsVersion();
  if (currentVersion < 1) {
    localStorage.setItem("AGENT", DEFAULT_SETTINGS.AGENT);
  }
};

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;

/**
 * Get the settings from local storage or use the default settings if not found
 */
export const getSettings = (): Settings => {
  const model = localStorage.getItem("LLM_MODEL");
  const customModel = localStorage.getItem("CUSTOM_LLM_MODEL");
  const usingCustomModel =
    localStorage.getItem("USING_CUSTOM_MODEL") === "true";
  const agent = localStorage.getItem("AGENT");
  const language = localStorage.getItem("LANGUAGE");
  const apiKey = localStorage.getItem("LLM_API_KEY");
  const confirmationMode = localStorage.getItem("CONFIRMATION_MODE") === "true";
  const securityAnalyzer = localStorage.getItem("SECURITY_ANALYZER");

  return {
    LLM_MODEL: model || DEFAULT_SETTINGS.LLM_MODEL,
    CUSTOM_LLM_MODEL: customModel || DEFAULT_SETTINGS.CUSTOM_LLM_MODEL,
    USING_CUSTOM_MODEL: usingCustomModel || DEFAULT_SETTINGS.USING_CUSTOM_MODEL,
    AGENT: agent || DEFAULT_SETTINGS.AGENT,
    LANGUAGE: language || DEFAULT_SETTINGS.LANGUAGE,
    LLM_API_KEY: apiKey || DEFAULT_SETTINGS.LLM_API_KEY,
    CONFIRMATION_MODE: confirmationMode || DEFAULT_SETTINGS.CONFIRMATION_MODE,
    SECURITY_ANALYZER: securityAnalyzer || DEFAULT_SETTINGS.SECURITY_ANALYZER,
  };
};

/**
 * Save the settings to local storage. Only valid settings are saved.
 * @param settings - the settings to save
 */
export const saveSettings = (settings: Partial<Settings>) => {
  Object.keys(settings).forEach((key) => {
    const isValid = validKeys.includes(key as keyof Settings);
    const value = settings[key as keyof Settings];

    if (isValid && typeof value !== "undefined")
      localStorage.setItem(key, value.toString());
  });
  localStorage.setItem("SETTINGS_VERSION", LATEST_SETTINGS_VERSION.toString());
};

/**
 * Get the difference between the current settings and the provided settings.
 * Useful for notifying the user of exact changes.
 *
 * @example
 * // Assuming the current settings are: { LLM_MODEL: "gpt-4o", AGENT: "CodeActAgent", LANGUAGE: "en" }
 * const updatedSettings = getSettingsDifference({ LLM_MODEL: "gpt-4o", AGENT: "OTHER_AGENT", LANGUAGE: "en" });
 * // updatedSettings = { AGENT: "OTHER_AGENT" }
 *
 * @param settings - the settings to compare
 * @returns the updated settings
 */
export const getSettingsDifference = (settings: Partial<Settings>) => {
  const currentSettings = getSettings();
  const updatedSettings: Partial<Settings> = {};

  Object.keys(settings).forEach((key) => {
    const typedKey = key as keyof Settings;
    if (
      validKeys.includes(typedKey) &&
      settings[typedKey] !== currentSettings[typedKey]
    ) {
      (updatedSettings[typedKey] as SettingsInput) = settings[
        typedKey
      ] as SettingsInput;
    }
  });

  return updatedSettings;
};
