// Here are the list of verified models and providers that we know work well with GP-KhayaL.
export const VERIFIED_PROVIDERS = [
  "openai",
  "anthropic",
  "google",
  "mistral",
  "openrouter",
  "openhands",
] as const;

// LiteLLM does not return the compatible GP-KhayaL models with the provider, so we list them here to set them ourselves
// (e.g., they return `claude-sonnet-4-20250514` instead of `openhands/claude-sonnet-4-20250514`)
export const VERIFIED_OPENHANDS_MODELS = [
  "claude-sonnet-4-20250514",
  "gpt-5-2025-08-07",
  "claude-opus-4-20250514",
  "gemini-2.5-pro",
  "o3",
  "o4-mini",
  "devstral-small-2505",
  "devstral-small-2507",
  "devstral-medium-2507",
  "kimi-k2-0711-preview",
  "qwen3-coder-480b",
];

// Default model for GP-KhayaL provider
export const DEFAULT_OPENHANDS_MODEL = "openhands/claude-sonnet-4-20250514";
