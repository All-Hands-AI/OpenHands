import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { openHands } from "#/api/open-hands-axios";
import { I18nKey } from "#/i18n/declaration";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

interface ConfigureIntegrationData {
  workspace: string;
  webhookSecret: string;
  serviceAccountEmail: string;
  serviceAccountApiKey: string;
  isActive: boolean;
}

export function useConfigureIntegration(
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
    mutationFn: async (data: ConfigureIntegrationData) => {
      const input = {
        workspace_name: data.workspace,
        webhook_secret: data.webhookSecret,
        svc_acc_email: data.serviceAccountEmail,
        svc_acc_api_key: data.serviceAccountApiKey,
        is_active: data.isActive,
      };

      const response = await openHands.post(
        `/integration/${platform}/workspaces`,
        input,
      );

      const { authorizationUrl } = response.data;

      if (authorizationUrl) {
        window.location.href = authorizationUrl;
      } else {
        throw new Error("Could not get authorization URL from the server.");
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
