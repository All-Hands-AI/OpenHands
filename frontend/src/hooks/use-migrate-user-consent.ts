import React from "react";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { useSaveSettings } from "./mutation/use-save-settings";
import { useDisableApiOnTos } from "./use-disable-api-on-tos";

export const useMigrateUserConsent = () => {
  const { mutate: saveUserSettings } = useSaveSettings();
  const disableApiCalls = useDisableApiOnTos();

  /**
   * Migrate user consent to the settings store on the server.
   */
  const migrateUserConsent = React.useCallback(
    async (args?: { handleAnalyticsWasPresentInLocalStorage: () => void }) => {
      // Skip migration on TOS page
      if (disableApiCalls) {
        return;
      }

      const userAnalyticsConsent = localStorage.getItem("analytics-consent");

      if (userAnalyticsConsent) {
        args?.handleAnalyticsWasPresentInLocalStorage();

        await saveUserSettings(
          { user_consents_to_analytics: userAnalyticsConsent === "true" },
          {
            onSuccess: () => {
              handleCaptureConsent(userAnalyticsConsent === "true");
            },
          },
        );

        localStorage.removeItem("analytics-consent");
      }
    },
    [disableApiCalls],
  );

  return { migrateUserConsent };
};
