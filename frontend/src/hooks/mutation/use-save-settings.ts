import { useMutation, useQueryClient } from "@tanstack/react-query";
import { DEFAULT_SETTINGS } from "#/services/settings";
import OpenHands from "#/api/open-hands";
import { PostSettings, PostApiSettings } from "#/types/settings";
import { useSettings } from "../query/use-settings";

const saveSettingsMutationFn = async (settings: Partial<PostSettings>) => {
  const apiSettings: Partial<PostApiSettings> = {
    llm_model: settings.LLM_MODEL,
    llm_base_url: settings.LLM_BASE_URL,
    agent: settings.AGENT || DEFAULT_SETTINGS.AGENT,
    language: settings.LANGUAGE || DEFAULT_SETTINGS.LANGUAGE,
    confirmation_mode: settings.CONFIRMATION_MODE,
    security_analyzer: settings.SECURITY_ANALYZER,
    llm_api_key:
      settings.llm_api_key === ""
        ? ""
        : settings.llm_api_key?.trim() || undefined,
    remote_runtime_resource_factor: settings.REMOTE_RUNTIME_RESOURCE_FACTOR,
    enable_default_condenser: settings.ENABLE_DEFAULT_CONDENSER,
    enable_sound_notifications: settings.ENABLE_SOUND_NOTIFICATIONS,
    user_consents_to_analytics: settings.user_consents_to_analytics,
    enable_proactive_conversation_starters:
      settings.ENABLE_PROACTIVE_CONVERSATION_STARTERS,
  };

  await OpenHands.saveSettings(apiSettings);
};

export const useSaveSettings = () => {
  const queryClient = useQueryClient();
  const { data: currentSettings } = useSettings();

  return useMutation({
    mutationFn: async (settings: Partial<PostSettings>) => {
      const newSettings = { ...currentSettings, ...settings };
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
