import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiSettings } from "#/services/settings";
import OpenHands from "#/api/open-hands";

const saveSettingsMutationFn = async (settings: Partial<ApiSettings>) => {
  await OpenHands.saveSettings(settings);
};

export const useSaveSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: saveSettingsMutationFn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
};
