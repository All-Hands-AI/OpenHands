import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiSettings, Settings } from "#/services/settings";
import OpenHands from "#/api/open-hands";
import { updateSettingsVersion } from "#/utils/settings-utils";
import { useAuth } from "#/context/auth-context";
import { useSettingsUpToDate } from "#/context/settings-up-to-date-context";

const saveSettingsMutationFn = async (settings: Partial<Settings>) => {
  const apiSettings: Partial<ApiSettings> = {
    llm_model: settings.LLM_MODEL,
    llm_base_url: settings.LLM_BASE_URL,
    agent: settings.AGENT,
    language: settings.LANGUAGE,
    confirmation_mode: settings.CONFIRMATION_MODE,
    security_analyzer: settings.SECURITY_ANALYZER,
    llm_api_key: settings.LLM_API_KEY,
  };

  await OpenHands.saveSettings(apiSettings);
};

export const useSaveSettings = () => {
  const queryClient = useQueryClient();
  const { logout } = useAuth();
  const { setIsUpToDate } = useSettingsUpToDate();

  return useMutation({
    mutationFn: saveSettingsMutationFn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      updateSettingsVersion(logout);
      setIsUpToDate(true);
    },
  });
};
