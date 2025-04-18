enum ArgConfigType {
  LLM_MODEL = "LLM_MODEL",
  AGENT = "AGENT",
  LANGUAGE = "LANGUAGE",
  LLM_API_KEY_SET = "LLM_API_KEY_SET",
}

const SupportedSettings: string[] = [
  ArgConfigType.LLM_MODEL,
  ArgConfigType.AGENT,
  ArgConfigType.LANGUAGE,
  ArgConfigType.LLM_API_KEY_SET,
];

export { ArgConfigType, SupportedSettings };
