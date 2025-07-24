import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { openHands } from "#/api/open-hands-axios";
import { I18nKey } from "#/i18n/declaration";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

export function useLinkIntegration(
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
    mutationFn: async (workspace: string) => {
      const input = {
        workspace,
      };

      const response = await openHands.post(
        `/integration/${platform}/link`,
        input,
      );

      const { success, redirect, authorizationUrl } = response.data;

      if (success) {
        if (redirect) {
          if (authorizationUrl) {
            window.location.href = authorizationUrl;
          } else {
            throw new Error("Could not get authorization URL from the server.");
          }
        } else {
          window.location.reload();
        }
      } else {
        throw new Error("Link integration failed");
      }

      return response.data;
    },
    onSuccess: () => {
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
