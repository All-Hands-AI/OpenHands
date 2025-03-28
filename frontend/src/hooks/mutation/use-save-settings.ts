import { useMutation, useQueryClient } from "@tanstack/react-query";
import { DEFAULT_SETTINGS } from "#/services/settings";
import OpenHands from "#/api/open-hands";
import { useSettings } from "../query/use-settings";
import { UserSettings } from "#/api/settings-service/settings-service.types";
import { SettingsService } from "#/api/settings-service/settings-service.api";

const saveSettingsMutationFn = async (
  settings: Partial<UserSettings> | null,
) => {
  // If settings is null, we're resetting
  if (settings === null) {
    await OpenHands.resetSettings();
    return;
  }

  const safeSettings: Partial<UserSettings> = {
    ...settings,
    agent: settings.agent || DEFAULT_SETTINGS.agent,
    language: settings.language || DEFAULT_SETTINGS.language,
    llm_api_key:
      settings.llm_api_key === ""
        ? ""
        : settings.llm_api_key?.trim() || undefined,
  };

  await SettingsService.saveSettings(safeSettings);
};

export const useSaveSettings = () => {
  const queryClient = useQueryClient();
  const { data: currentSettings } = useSettings();

  return useMutation({
    mutationFn: async (settings: Partial<UserSettings> | null) => {
      if (settings === null) {
        await saveSettingsMutationFn(null);
        return;
      }

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
