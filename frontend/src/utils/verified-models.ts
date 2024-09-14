// Here are the list of verified models and providers that we know work well with OpenHands.
export const VERIFIED_PROVIDERS = ["openai", "azure", "anthropic"];
export const VERIFIED_MODELS = ["gpt-4o", "claude-3-5-sonnet-20240620"];

// LiteLLM does not return OpenAI models with the provider, so we list them here to set them ourselves for consistency
// (e.g., they return `gpt-4o` instead of `openai/gpt-4o`)
export const VERIFIED_OPENAI_MODELS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-4",
  "gpt-4-32k",
  "o1-mini",
  "o1-preview",
];

// LiteLLM does not return the compatible Anthropic models with the provider, so we list them here to set them ourselves
// (e.g., they return `claude-3-5-sonnet-20240620` instead of `anthropic/claude-3-5-sonnet-20240620`)
export const VERIFIED_ANTHROPIC_MODELS = [
  "claude-2",
  "claude-2.1",
  "claude-3-5-sonnet-20240620",
  "claude-3-haiku-20240307",
  "claude-3-opus-20240229",
  "claude-3-sonnet-20240229",
  "claude-instant-1",
  "claude-instant-1.2",
];
