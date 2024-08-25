// Here are the list of verified models and providers that we know work well with OpenHands.
export const VERIFIED_PROVIDERS = ["openai", "azure", "anthropic"];
export const VERIFIED_MODELS = ["gpt-4o", "claude-3-5-sonnet-20240620-v1:0"];

// LiteLLM does not return OpenAI models with the provider, so we list them here to set them ourselves for consistency
// (e.g., they return `gpt-4o` instead of `openai/gpt-4o`)
export const VERIFIED_OPENAI_MODELS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-4",
  "gpt-4-32k",
  "gpt-3.5-turbo",
];
