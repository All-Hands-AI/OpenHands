import { Settings } from "#/services/settings";

const extractBasicFormData = (formData: FormData) => {
  const provider = formData.get("llm-provider")?.toString();
  const model = formData.get("llm-model")?.toString();

  const LLM_MODEL = `${provider}/${model}`.toLowerCase();
  const LLM_API_KEY = formData.get("api-key")?.toString();
  const AGENT = formData.get("agent")?.toString();
  const LANGUAGE = formData.get("language")?.toString();

  return {
    LLM_MODEL,
    LLM_API_KEY,
    AGENT,
    LANGUAGE,
  };
};

const extractAdvancedFormData = (formData: FormData) => {
  const keys = Array.from(formData.keys());
  const isUsingAdvancedOptions = keys.includes("use-advanced-options");

  let CUSTOM_LLM_MODEL: string | undefined;
  let LLM_BASE_URL: string | undefined;
  let CONFIRMATION_MODE = false;
  let SECURITY_ANALYZER: string | undefined;

  if (isUsingAdvancedOptions) {
    CUSTOM_LLM_MODEL = formData.get("custom-model")?.toString();
    LLM_BASE_URL = formData.get("base-url")?.toString();
    CONFIRMATION_MODE = keys.includes("confirmation-mode");
    if (CONFIRMATION_MODE) {
      // only set securityAnalyzer if confirmationMode is enabled
      SECURITY_ANALYZER = formData.get("security-analyzer")?.toString();
    }
  }

  return {
    CUSTOM_LLM_MODEL,
    LLM_BASE_URL,
    CONFIRMATION_MODE,
    SECURITY_ANALYZER,
  };
};

const extractSettings = (formData: FormData): Partial<Settings> => {
  const { LLM_MODEL, LLM_API_KEY, AGENT, LANGUAGE } =
    extractBasicFormData(formData);

  const {
    CUSTOM_LLM_MODEL,
    LLM_BASE_URL,
    CONFIRMATION_MODE,
    SECURITY_ANALYZER,
  } = extractAdvancedFormData(formData);

  return {
    LLM_MODEL: CUSTOM_LLM_MODEL || LLM_MODEL,
    LLM_API_KEY,
    AGENT,
    LANGUAGE,
    LLM_BASE_URL,
    CONFIRMATION_MODE,
    SECURITY_ANALYZER,
  };
};

const saveSettingsView = (view: "basic" | "advanced") => {
  localStorage.setItem(
    "use-advanced-options",
    view === "advanced" ? "true" : "false",
  );
};

export { extractSettings, saveSettingsView };
