import { openHands } from "#/api/open-hands-axios";

export const LATEST_SETTINGS_VERSION = 5;

export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string | null;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
};

export type ApiSettings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  confirmation_mode: boolean;
  security_analyzer: string;
};

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: null,
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

// TODO: localStorage settings are deprecated. Remove this after 1/31/2025
export const getLocalStorageSettings = (): Settings => {
  const llmModel = localStorage.getItem("LLM_MODEL");
  const baseUrl = localStorage.getItem("LLM_BASE_URL");
  const agent = localStorage.getItem("AGENT");
  const language = localStorage.getItem("LANGUAGE");
  const llmApiKey = localStorage.getItem("LLM_API_KEY");
  const confirmationMode = localStorage.getItem("CONFIRMATION_MODE") === "true";
  const securityAnalyzer = localStorage.getItem("SECURITY_ANALYZER");

  return {
    LLM_MODEL: llmModel || DEFAULT_SETTINGS.LLM_MODEL,
    LLM_BASE_URL: baseUrl || DEFAULT_SETTINGS.LLM_BASE_URL,
    AGENT: agent || DEFAULT_SETTINGS.AGENT,
    LANGUAGE: language || DEFAULT_SETTINGS.LANGUAGE,
    LLM_API_KEY: llmApiKey || DEFAULT_SETTINGS.LLM_API_KEY,
    CONFIRMATION_MODE: confirmationMode || DEFAULT_SETTINGS.CONFIRMATION_MODE,
    SECURITY_ANALYZER: securityAnalyzer || DEFAULT_SETTINGS.SECURITY_ANALYZER,
  };
};

/**
 * Save the settings to the server. Only valid settings are saved.
 * @param settings - the settings to save
 */
export const saveSettings = async (
  settings: Partial<Settings>,
): Promise<boolean> => {
  try {
    const apiSettings = {
      llm_model: settings.LLM_MODEL || null,
      llm_base_url: settings.LLM_BASE_URL || null,
      agent: settings.AGENT || null,
      language: settings.LANGUAGE || null,
      confirmation_mode: settings.CONFIRMATION_MODE || null,
      security_analyzer: settings.SECURITY_ANALYZER || null,
      llm_api_key: settings.LLM_API_KEY || null,
    };

    const { data } = await openHands.post("/api/settings", apiSettings);
    return data;
  } catch (error) {
    // Error handled by returning false
    return false;
  }
};

export const maybeMigrateSettings = async (logout: () => void) => {
  // Sometimes we ship major changes, like a new default agent.
  // In this case, we may want to override a previous choice made by the user.
  const currentVersion = getCurrentSettingsVersion();

  if (currentVersion < 1) {
    localStorage.setItem("AGENT", DEFAULT_SETTINGS.AGENT);
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

  if (currentVersion < 5) {
    const localSettings = getLocalStorageSettings();
    await saveSettings(localSettings);
  }
};

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;

/**
 * Get the settings from the server or use the default settings if not found
 */
export const getSettings = async (): Promise<Settings> => {
  try {
    const { data: apiSettings } =
      await openHands.get<ApiSettings>("/api/settings");
    return {
      LLM_MODEL: apiSettings.llm_model,
      LLM_BASE_URL: apiSettings.llm_base_url,
      AGENT: apiSettings.agent,
      LANGUAGE: apiSettings.language,
      CONFIRMATION_MODE: apiSettings.confirmation_mode,
      SECURITY_ANALYZER: apiSettings.security_analyzer,
      LLM_API_KEY: "",
    };
  } catch (error) {
    // @ts-expect-error we don't have a type annotation for the response
    if (error.response?.status !== 404) {
      throw error;
    }
  }
  // FIXME: remove local storage settings after 1/31/2025
  const localSettings = getLocalStorageSettings();
  await saveSettings(localSettings);
  return localSettings;
};
