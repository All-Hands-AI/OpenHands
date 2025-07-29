import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { openHands } from "#/api/open-hands-axios";
import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

export function useUnlinkIntegration(
  platform: "jira" | "jira-dc" | "linear",
  {
    onSettled,
  }: {
    onSettled: () => void;
  },
) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: () => openHands.post(`/integration/${platform}/unlink`),
    onSuccess: () => {
      displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
      queryClient.invalidateQueries({
        queryKey: ["integration-status", platform],
      });
    },
    onError: (error) => {
      const errorMessage = retrieveAxiosErrorMessage(error);
      displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
    },
    onSettled,
  });
}
