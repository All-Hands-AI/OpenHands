import { Settings } from "#/services/settings";

const extractBasicFormData = (formData: FormData) => {
  const provider = formData.get("llm-provider")?.toString();
  const model = formData.get("llm-model")?.toString();

  const llm_model = `${provider}/${model}`.toLowerCase();
  const llm_api_key = formData.get("api-key")?.toString();
  const agent = formData.get("agent")?.toString();
  const language = formData.get("language")?.toString();

  return {
    llm_model,
    llm_api_key,
    agent,
    language,
  };
};

const extractAdvancedFormData = (formData: FormData) => {
  const keys = Array.from(formData.keys());
  const isUsingAdvancedOptions = keys.includes("use-advanced-options");

  let custom_llm_model: string | undefined;
  let llm_base_url: string | undefined;
  let confirmation_mode = false;
  let security_analyzer: string | undefined;

  if (isUsingAdvancedOptions) {
    custom_llm_model = formData.get("custom-model")?.toString();
    llm_base_url = formData.get("base-url")?.toString();
    confirmation_mode = keys.includes("confirmation-mode");
    if (confirmation_mode) {
      // only set securityAnalyzer if confirmationMode is enabled
      security_analyzer = formData.get("security-analyzer")?.toString();
    }
  }

  return {
    custom_llm_model,
    llm_base_url,
    confirmation_mode,
    security_analyzer,
  };
};

const extractSettings = (formData: FormData): Partial<Settings> => {
  const { llm_model, llm_api_key, agent, language } =
    extractBasicFormData(formData);

  const {
    custom_llm_model,
    llm_base_url,
    confirmation_mode,
    security_analyzer,
  } = extractAdvancedFormData(formData);

  return {
    llm_model: custom_llm_model || llm_model,
    llm_api_key,
    agent,
    language,
    llm_base_url,
    confirmation_mode,
    security_analyzer,
  };
};

export { extractSettings };