import OpenHands from "#/api/open-hands";

export type Settings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string;
  confirmation_mode: boolean;
  security_analyzer: string;
};

export const DEFAULT_SETTINGS: Settings = {
  llm_model: "anthropic/claude-3-5-sonnet-20241022",
  llm_base_url: "",
  agent: "CodeActAgent",
  language: "en",
  llm_api_key: "",
  confirmation_mode: false,
  security_analyzer: "",
};

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
export const saveSettings = async (settings: Partial<Settings>): Promise<void> => {
  const currentSettings = await getSettings();
  const newSettings = {
    ...currentSettings,
    ...settings,
  };
  await OpenHands.storeSettings(newSettings);
};