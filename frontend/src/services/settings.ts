import { AvailableLanguages } from "#/i18n";

const LATEST_SETTINGS_VERSION = 1;

export type Settings = {
  LLM_MODEL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string;
  WORKSPACE_SUBDIR: string;
};

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "gpt-4o",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: "",
  WORKSPACE_SUBDIR: "",
};

export const getValueConverter = (
  key: keyof Partial<Settings>,
): ((s: string) => string) => {
  switch (key) {
    case "WORKSPACE_SUBDIR":
      return (value) => (value === "" ? "Workspace Root" : value);
    case "LANGUAGE":
      return (value) =>
        AvailableLanguages.find((l) => l.value === value)?.label || "";
    default:
      return (v) => v;
  }
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
  const agent = localStorage.getItem("AGENT");
  const language = localStorage.getItem("LANGUAGE");
  const apiKey = localStorage.getItem("LLM_API_KEY");
  const workspaceSubdir = localStorage.getItem("WORKSPACE_SUBDIR");

  return {
    LLM_MODEL: model || DEFAULT_SETTINGS.LLM_MODEL,
    AGENT: agent || DEFAULT_SETTINGS.AGENT,
    LANGUAGE: language || DEFAULT_SETTINGS.LANGUAGE,
    LLM_API_KEY: apiKey || DEFAULT_SETTINGS.LLM_API_KEY,
    WORKSPACE_SUBDIR: workspaceSubdir || DEFAULT_SETTINGS.WORKSPACE_SUBDIR,
  };
};

/**
 * Save the settings to local storage. Only valid settings are saved.
 * @param settings - the settings to save
 */
export const saveSettings = (settings: Partial<Settings>) => {
  Object.keys(settings).forEach((key) => {
    const isValidKey = validKeys.includes(key as keyof Settings);
    const value = settings[key as keyof Settings];
    if (isValidKey && typeof value !== "undefined")
      localStorage.setItem(key, value);
  });
  localStorage.setItem("SETTINGS_VERSION", LATEST_SETTINGS_VERSION.toString());
};

/**
 * Get the difference between two sets of settings.
 * Useful for notifying the user of exact changes.
 *
 * @example
 * // Assuming the current settings are:
 * const updatedSettings = getSettingsDifference(
 *  { LLM_MODEL: "gpt-4o", AGENT: "MonologueAgent", LANGUAGE: "en" },
 *  { LLM_MODEL: "gpt-4o", AGENT: "OTHER_AGENT", LANGUAGE: "en" }
 * )
 * // updatedSettings = { AGENT: "OTHER_AGENT" }
 *
 * @returns only the settings from `newSettings` that are different from `oldSettings`.
 */
export const getSettingsDifference = (
  oldSettings: Partial<Settings>,
  newSettings: Partial<Settings>,
) => {
  const updatedSettings: Partial<Settings> = {};
  Object.keys(newSettings).forEach((key) => {
    if (
      validKeys.includes(key as keyof Settings) &&
      newSettings[key as keyof Settings] !== oldSettings[key as keyof Settings]
    ) {
      updatedSettings[key as keyof Settings] =
        newSettings[key as keyof Settings];
    }
  });

  return updatedSettings;
};
