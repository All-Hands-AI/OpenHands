import { useMutation, useQueryClient } from "@tanstack/react-query";
import { DEFAULT_SETTINGS } from "#/services/settings";
import OpenHands from "#/api/open-hands";
import { PostSettings, PostApiSettings } from "#/types/settings";
import { useSettings } from "../query/use-settings";

const saveSettingsMutationFn = async (settings: Partial<PostSettings>) => {
  const resetLlmApiKey = settings.LLM_API_KEY === "";

  const apiSettings: Partial<PostApiSettings> = {
    llm_model: settings.LLM_MODEL,
    llm_base_url: settings.LLM_BASE_URL,
    agent: settings.AGENT || DEFAULT_SETTINGS.AGENT,
    language: settings.LANGUAGE || DEFAULT_SETTINGS.LANGUAGE,
    confirmation_mode: settings.CONFIRMATION_MODE,
    security_analyzer: settings.SECURITY_ANALYZER,
    llm_api_key: resetLlmApiKey
      ? ""
      : settings.LLM_API_KEY?.trim() || undefined,
    remote_runtime_resource_factor: settings.REMOTE_RUNTIME_RESOURCE_FACTOR,
    enable_default_condenser: settings.ENABLE_DEFAULT_CONDENSER,
    enable_sound_notifications: settings.ENABLE_SOUND_NOTIFICATIONS,
    user_consents_to_analytics: settings.user_consents_to_analytics,
    provider_tokens: settings.provider_tokens,
    custom_secrets: settings.custom_secrets,
    unset_tokens: settings.unset_tokens,
  };

  await OpenHands.saveSettings(apiSettings);
};

export const useSaveSettings = () => {
  const queryClient = useQueryClient();
  const { data: currentSettings } = useSettings();

  return useMutation({
    mutationFn: async (settings: Partial<PostSettings>) => {
      const newSettings = { ...currentSettings, ...settings };

      // Temp hack for reset logic
      if (
        settings.LLM_API_KEY === undefined &&
        settings.LLM_BASE_URL === undefined &&
        settings.LLM_MODEL === undefined
      ) {
        delete newSettings.LLM_API_KEY;
        delete newSettings.LLM_BASE_URL;
        delete newSettings.LLM_MODEL;
      }

      await saveSettingsMutationFn(newSettings);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    meta: {
      disableToast: true,
    },
  });
};
