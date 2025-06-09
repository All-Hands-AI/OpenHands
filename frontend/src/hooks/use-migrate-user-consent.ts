import React from "react";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { useSaveSettings } from "./mutation/use-save-settings";

export const useMigrateUserConsent = () => {
  const { mutate: saveUserSettings } = useSaveSettings();

  /**
   * Migrate user consent to the settings store on the server.
   */
  const migrateUserConsent = React.useCallback(
    async (args?: { handleAnalyticsWasPresentInLocalStorage: () => void }) => {
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
    [],
  );

  return { migrateUserConsent };
};
