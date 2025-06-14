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
  EMAIL: "",
  EMAIL_VERIFIED: true, // Default to true to avoid restricting access unnecessarily
  MCP_CONFIG: {
    sse_servers: [],
    stdio_servers: [
      {
        name: "Context7",
        command: "npx",
        args: ["-y", "@upstash/context7-mcp@latest"],
        env: {},
      },
      {
        name: "Firecrawl",
        command: "npx",
        args: ["-y", "firecrawl-mcp"],
        env: {
          FIRECRAWL_API_URL: "https://crawl.armand0e.online",
          FIRECRAWL_API_KEY: "fc-1234567890",
          FIRECRAWL_RETRY_MAX_ATTEMPTS: "10",
          FIRECRAWL_RETRY_INITIAL_DELAY: "400",
        },
      },
    ],
  },
};

/**
 * Get the default settings
 */
export const getDefaultSettings = (): Settings => DEFAULT_SETTINGS;
