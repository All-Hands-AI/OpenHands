import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { openHands } from "#/api/open-hands-axios";
import { I18nKey } from "#/i18n/declaration";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

export function useLinearInstall() {
  const { t } = useTranslation();

  return useMutation({
    mutationFn: async () => {
      const response = await openHands.post(
        "/integration/linear/workspaces/link",
        {},
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
        throw new Error("Linear installation failed");
      }

      return response.data;
    },
    onError: (error) => {
      const errorMessage = retrieveAxiosErrorMessage(error);
      displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
    },
  });
}
