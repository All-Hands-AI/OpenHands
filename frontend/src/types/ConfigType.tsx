enum ArgConfigType {
  LLM_MODEL = "LLM_MODEL",
  AGENT = "AGENT",
  LANGUAGE = "LANGUAGE",
  LLM_API_KEY = "LLM_API_KEY",
  WORKSPACE = "WORKSPACE",
}

const SupportedSettings: string[] = [
  ArgConfigType.LLM_MODEL,
  ArgConfigType.AGENT,
  ArgConfigType.LANGUAGE,
  ArgConfigType.LLM_API_KEY,
  ArgConfigType.WORKSPACE,
];

export { ArgConfigType, SupportedSettings };
