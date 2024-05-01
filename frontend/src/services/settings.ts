export type Settings = {
  LLM_MODEL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string;
};

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "gpt-3.5-turbo",
  AGENT: "MonologueAgent",
  LANGUAGE: "en",
  LLM_API_KEY: "",
};

const validKeys = Object.keys(DEFAULT_SETTINGS) as (keyof Settings)[];

/**
 * Get the settings from local storage or use the default settings if not found
 */
export const getSettings = (): Settings => {
  const model = localStorage.getItem("LLM_MODEL");
  const agent = localStorage.getItem("AGENT");
  const language = localStorage.getItem("LANGUAGE");
  const apiKey = localStorage.getItem(`API_KEY_${model}`);

  return {
    LLM_MODEL: model || DEFAULT_SETTINGS.LLM_MODEL,
    AGENT: agent || DEFAULT_SETTINGS.AGENT,
    LANGUAGE: language || DEFAULT_SETTINGS.LANGUAGE,
    LLM_API_KEY: apiKey || DEFAULT_SETTINGS.LLM_API_KEY,
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

    if (isValid && value) localStorage.setItem(key, value);
  });
};

/**
 * Get the difference between the current settings and the provided settings.
 * Useful for notifiying the user of exact changes.
 *
 * @example
 * // Assuming the current settings are: { LLM_MODEL: "gpt-3.5", AGENT: "MonologueAgent", LANGUAGE: "en" }
 * const updatedSettings = getSettingsDifference({ LLM_MODEL: "gpt-3.5", AGENT: "OTHER_AGENT", LANGUAGE: "en" });
 * // updatedSettings = { AGENT: "OTHER_AGENT" }
 *
 * @param settings - the settings to compare
 * @returns the updated settings
 */
export const getSettingsDifference = (settings: Partial<Settings>) => {
  const currentSettings = getSettings();
  const updatedSettings: Partial<Settings> = {};

  Object.keys(settings).forEach((key) => {
    if (
      validKeys.includes(key as keyof Settings) &&
      settings[key as keyof Settings] !== currentSettings[key as keyof Settings]
    ) {
      updatedSettings[key as keyof Settings] = settings[key as keyof Settings];
    }
  });

  return updatedSettings;
};
