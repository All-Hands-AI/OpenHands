import { Settings } from "#/types/settings";

export const LATEST_SETTINGS_VERSION = 5;

export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "anthropic/claude-sonnet-4-20250514",
  LLM_BASE_URL: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  LLM_API_KEY_SET: false,
  SEARCH_API_KEY_SET: false,
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
  REMOTE_RUNTIME_RESOURCE_FACTOR: 1,
  PROVIDER_TOKENS_SET: {},
  ENABLE_DEFAULT_CONDENSER: true,
  ENABLE_SOUND_NOTIFICATIONS: false,
  USER_CONSENTS_TO_ANALYTICS: false,
  ENABLE_PROACTIVE_CONVERSATION_STARTERS: false,
  SEARCH_API_KEY: "",
  IS_NEW_USER: true,
  MAX_BUDGET_PER_TASK: null,
  EMAIL: "",
  EMAIL_VERIFIED: true, // Default to true to avoid restricting access unnecessarily
  MCP_CONFIG: {
    sse_servers: [],
    stdio_servers: [],
  },
  TEMPERATURE: 0.0, // Aligning with backend default temperature value
  TOP_P: 1.0,
  MAX_OUTPUT_TOKENS: null,
  MAX_INPUT_TOKENS: null,
  MAX_MESSAGE_CHARS: 30000,
  INPUT_COST_PER_TOKEN: null,
  OUTPUT_COST_PER_TOKEN: null,
  // Agent Configuration Parameters
  ENABLE_BROWSING: true,
  ENABLE_LLM_EDITOR: false,
  ENABLE_EDITOR: true,
  ENABLE_JUPYTER: true,
  ENABLE_CMD: true,
  ENABLE_THINK: true,
  ENABLE_FINISH: true,
  ENABLE_PROMPT_EXTENSIONS: true,
  DISABLED_MICROAGENTS: [],
  ENABLE_HISTORY_TRUNCATION: true,
};

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;
