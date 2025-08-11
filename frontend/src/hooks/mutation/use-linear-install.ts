import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { I18nKey } from "#/i18n/declaration";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

export function useLinearInstall() {
  const { t } = useTranslation();

  return useMutation({
    mutationFn: async () =>
      // For now, we'll return the Linear installation URL
      // This could be enhanced to call a backend endpoint if needed
      ({
        installationUrl:
          "https://app.all-hands-dev/integration/linear/workspaces",
      }),
    onSuccess: (data) => {
      // Redirect to the Linear installation URL
      window.location.href = data.installationUrl;
    },
    onError: (error) => {
      displayErrorToast(
        error instanceof Error ? error.message : t(I18nKey.ERROR$GENERIC),
      );
    },
  });
}
