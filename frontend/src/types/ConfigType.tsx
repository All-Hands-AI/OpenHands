enum ArgConfigType {
  LLM_MODEL = "LLM_MODEL",
  AGENT = "AGENT",
  LANGUAGE = "LANGUAGE",
}

const SupportedSettings: string[] = [
  ArgConfigType.LLM_MODEL,
  ArgConfigType.AGENT,
  ArgConfigType.LANGUAGE,
];

export { ArgConfigType, SupportedSettings };
