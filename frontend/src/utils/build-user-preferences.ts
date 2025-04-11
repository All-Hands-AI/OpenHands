import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { PostSettings } from "#/types/settings";

const REMOTE_RUNTIME_OPTIONS = [
  { key: "1", label: "Standard" },
  { key: "2", label: "Enhanced" },
  { key: "4", label: "Premium" },
];

/**
 * Builds user preferences object from form data and configuration flags
 * @param formData - Form data containing user preferences
 * @param isLLMKeySet - Flag indicating if LLM key is already set
 * @param shouldHandleSpecialSaasCase - Flag for special SaaS case handling
 * @param confirmationModeIsEnabled - Flag for confirmation mode status
 * @returns User settings configuration object
 */
export const buildUserPreferences = (
  formData: FormData,
  isLLMKeySet: boolean | undefined,
  shouldHandleSpecialSaasCase: boolean | undefined,
  confirmationModeIsEnabled: boolean,
): Partial<PostSettings> & { user_consents_to_analytics: boolean } => {
  const languageLabel = formData.get("language-input")?.toString();
  const languageValue = AvailableLanguages.find(
    ({ label }) => label === languageLabel,
  )?.value;

  const llmProvider = formData.get("llm-provider-input")?.toString();
  const llmModel = formData.get("llm-model-input")?.toString();
  const fullLlmModel = `${llmProvider}/${llmModel}`.toLowerCase();
  const customLlmModel = formData.get("llm-custom-model-input")?.toString();

  const rawRemoteRuntimeResourceFactor = formData
    .get("runtime-settings-input")
    ?.toString();
  const remoteRuntimeResourceFactor = REMOTE_RUNTIME_OPTIONS.find(
    ({ label }) => label === rawRemoteRuntimeResourceFactor,
  )?.key;

  const userConsentsToAnalytics =
    formData.get("enable-analytics-switch")?.toString() === "on";
  const enableMemoryCondenser =
    formData.get("enable-memory-condenser-switch")?.toString() === "on";
  const enableSoundNotifications =
    formData.get("enable-sound-notifications-switch")?.toString() === "on";
  const llmBaseUrl = formData.get("base-url-input")?.toString().trim() || "";
  const inputApiKey = formData.get("llm-api-key-input")?.toString() || "";
  const llmApiKey =
    inputApiKey === "" && isLLMKeySet
      ? undefined // don't update if it's already set and input is empty
      : inputApiKey; // otherwise use the input value

  const githubToken = formData.get("github-token-input")?.toString();
  const gitlabToken = formData.get("gitlab-token-input")?.toString();
  // we don't want the user to be able to modify these settings in SaaS
  const finalLlmModel = shouldHandleSpecialSaasCase
    ? undefined
    : customLlmModel || fullLlmModel;
  const finalLlmBaseUrl = shouldHandleSpecialSaasCase ? undefined : llmBaseUrl;
  const finalLlmApiKey = shouldHandleSpecialSaasCase ? undefined : llmApiKey;

  const newSettings = {
    provider_tokens:
      githubToken || gitlabToken
        ? {
            github: githubToken || "",
            gitlab: gitlabToken || "",
          }
        : undefined,
    LANGUAGE: languageValue,
    user_consents_to_analytics: userConsentsToAnalytics,
    ENABLE_DEFAULT_CONDENSER: enableMemoryCondenser,
    ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
    LLM_MODEL: finalLlmModel,
    LLM_BASE_URL: finalLlmBaseUrl,
    llm_api_key: finalLlmApiKey,
    AGENT: formData.get("agent-input")?.toString(),
    SECURITY_ANALYZER:
      formData.get("security-analyzer-input")?.toString() || "",
    REMOTE_RUNTIME_RESOURCE_FACTOR:
      remoteRuntimeResourceFactor !== null
        ? Number(remoteRuntimeResourceFactor)
        : DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
    CONFIRMATION_MODE: confirmationModeIsEnabled,
  };

  return newSettings;
};
