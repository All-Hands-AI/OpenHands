// These are provider names, not user-facing text
export const PROVIDER_NAME_MAP: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google (Gemini)",
  mistral: "Mistral",
  openrouter: "OpenRouter",
  openhands: "GP-KhayaL",
};

export const mapProvider = (provider: string) =>
  Object.keys(PROVIDER_NAME_MAP).includes(provider)
    ? PROVIDER_NAME_MAP[provider as keyof typeof PROVIDER_NAME_MAP]
    : provider;

export const getProviderId = (displayName: string): string => {
  const entry = Object.entries(PROVIDER_NAME_MAP).find(
    ([, value]) => value === displayName,
  );
  return entry ? entry[0] : displayName;
};
