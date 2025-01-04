import OpenHands from "#/api/open-hands";

export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY: string | null;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
  REMOTE_RUNTIME_RESOURCE_FACTOR: number;
};

export type ApiSettings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  confirmation_mode: boolean;
  security_analyzer: string;
  remote_runtime_resource_factor: number;
};

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY: null,
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
  REMOTE_RUNTIME_RESOURCE_FACTOR: 1,
};

// TODO: localStorage settings are deprecated. Remove this after 1/31/2025
/**
 * Get the settings from local storage
 * @returns the settings from local storage
 * @deprecated
 */
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
    REMOTE_RUNTIME_RESOURCE_FACTOR:
      DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
  };
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
    const apiSettings = await OpenHands.getSettings();
    if (apiSettings != null) {
      return {
        LLM_MODEL: apiSettings.llm_model || DEFAULT_SETTINGS.LLM_MODEL,
        LLM_BASE_URL: apiSettings.llm_base_url || DEFAULT_SETTINGS.LLM_BASE_URL,
        AGENT: apiSettings.agent || DEFAULT_SETTINGS.AGENT,
        LANGUAGE: apiSettings.language || DEFAULT_SETTINGS.LANGUAGE,
        CONFIRMATION_MODE:
          apiSettings.confirmation_mode ?? DEFAULT_SETTINGS.CONFIRMATION_MODE,
        SECURITY_ANALYZER:
          apiSettings.security_analyzer || DEFAULT_SETTINGS.SECURITY_ANALYZER,
        LLM_API_KEY: apiSettings.llm_api_key ?? DEFAULT_SETTINGS.LLM_API_KEY,
        REMOTE_RUNTIME_RESOURCE_FACTOR:
          apiSettings.remote_runtime_resource_factor ??
          DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
      };
    }
  } catch (error) {
    // If API fails, fallback to localStorage
  }
  return getLocalStorageSettings();
};
