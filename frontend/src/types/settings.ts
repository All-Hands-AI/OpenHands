export const ProviderOptions = {
  github: "github",
  gitlab: "gitlab",
  bitbucket: "bitbucket",
} as const;

export type Provider = keyof typeof ProviderOptions;

export type ProviderToken = {
  token: string;
  host: string | null;
};

export type MCPSSEServer = {
  url: string;
  api_key?: string;
};

export type MCPStdioServer = {
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
};

export type MCPConfig = {
  sse_servers: (string | MCPSSEServer)[];
  stdio_servers: MCPStdioServer[];
};

export type Settings = {
  LLM_MODEL: string;
  LLM_BASE_URL: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_API_KEY_SET: boolean;
  SEARCH_API_KEY_SET: boolean;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER: string;
  REMOTE_RUNTIME_RESOURCE_FACTOR: number | null;
  PROVIDER_TOKENS_SET: Partial<Record<Provider, string | null>>;
  ENABLE_DEFAULT_CONDENSER: boolean;
  ENABLE_SOUND_NOTIFICATIONS: boolean;
  ENABLE_PROACTIVE_CONVERSATION_STARTERS: boolean;
  USER_CONSENTS_TO_ANALYTICS: boolean | null;
  SEARCH_API_KEY?: string;
  IS_NEW_USER?: boolean;
  MCP_CONFIG?: MCPConfig;
  MAX_BUDGET_PER_TASK: number | null;
  EMAIL?: string;
  EMAIL_VERIFIED?: boolean;
};

export type ApiSettings = {
  llm_model: string;
  llm_base_url: string;
  agent: string;
  language: string;
  llm_api_key: string | null;
  llm_api_key_set: boolean;
  search_api_key_set: boolean;
  confirmation_mode: boolean;
  security_analyzer: string;
  remote_runtime_resource_factor: number | null;
  enable_default_condenser: boolean;
  enable_sound_notifications: boolean;
  enable_proactive_conversation_starters: boolean;
  user_consents_to_analytics: boolean | null;
  search_api_key?: string;
  provider_tokens_set: Partial<Record<Provider, string | null>>;
  max_budget_per_task: number | null;
  mcp_config?: {
    sse_servers: (string | MCPSSEServer)[];
    stdio_servers: MCPStdioServer[];
  };
  email?: string;
  email_verified?: boolean;
};

export type PostSettings = Settings & {
  user_consents_to_analytics: boolean | null;
  llm_api_key?: string | null;
  search_api_key?: string;
  mcp_config?: MCPConfig;
};

export type PostApiSettings = ApiSettings & {
  user_consents_to_analytics: boolean | null;
  search_api_key?: string;
  mcp_config?: MCPConfig;
};
