// Sometimes we ship major changes, like a new default agent.

import React from "react";
import { useSettingsUpToDate } from "#/context/settings-up-to-date-context";
import {
  getCurrentSettingsVersion,
  DEFAULT_SETTINGS,
  getLocalStorageSettings,
} from "#/services/settings";
import { useSaveSettings } from "./mutation/use-save-settings";

// In this case, we may want to override a previous choice made by the user.
export const useMaybeMigrateSettings = () => {
  const { mutateAsync: saveSettings } = useSaveSettings();
  const { isUpToDate } = useSettingsUpToDate();

  const maybeMigrateSettings = async () => {
    const currentVersion = getCurrentSettingsVersion();

    if (currentVersion < 1) {
      localStorage.setItem("AGENT", DEFAULT_SETTINGS.AGENT);
    }
    if (currentVersion < 2) {
      const customModel = localStorage.getItem("CUSTOM_LLM_MODEL");
      if (customModel) {
        localStorage.setItem("LLM_MODEL", customModel);
      }
      localStorage.removeItem("CUSTOM_LLM_MODEL");
      localStorage.removeItem("USING_CUSTOM_MODEL");
    }
    if (currentVersion < 3) {
      localStorage.removeItem("token");
    }

    if (currentVersion < 4) {
      // We used to log out here, but it's breaking things
    }

    // Only save settings if user already previously saved settings
    // That way we avoid setting defaults for new users too early
    if (currentVersion !== 0 && currentVersion < 5) {
      const localSettings = getLocalStorageSettings();
      await saveSettings(localSettings);
    }
  };

  React.useEffect(() => {
    if (!isUpToDate) {
      maybeMigrateSettings();
    }
  }, []);
};
