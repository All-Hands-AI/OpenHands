import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ApiSettings,
  DEFAULT_SETTINGS,
  LATEST_SETTINGS_VERSION,
  Settings,
} from "#/services/settings";
import OpenHands from "#/api/open-hands";
import { useSettingsUpToDate } from "#/context/settings-up-to-date-context";

const saveSettingsMutationFn = async (settings: Partial<Settings>) => {
  const apiSettings: Partial<ApiSettings> = {
    llm_model: settings.LLM_MODEL,
    llm_base_url: settings.LLM_BASE_URL,
    agent: settings.AGENT || DEFAULT_SETTINGS.AGENT,
    language: settings.LANGUAGE || DEFAULT_SETTINGS.LANGUAGE,
    confirmation_mode: settings.CONFIRMATION_MODE,
    security_analyzer: settings.SECURITY_ANALYZER,
    llm_api_key: settings.LLM_API_KEY?.trim() || undefined,
  };

  await OpenHands.saveSettings(apiSettings);
};

export const useSaveSettings = () => {
  const queryClient = useQueryClient();
  const { isUpToDate, setIsUpToDate } = useSettingsUpToDate();

  return useMutation({
    mutationFn: saveSettingsMutationFn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      if (!isUpToDate) {
        localStorage.setItem(
          "SETTINGS_VERSION",
          LATEST_SETTINGS_VERSION.toString(),
        );
        setIsUpToDate(true);
      }
    },
  });
};
