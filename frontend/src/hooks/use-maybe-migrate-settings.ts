// Sometimes we ship major changes, like a new default agent.

import React from "react";
import { useCurrentSettings } from "#/context/settings-context";
import {
  getCurrentSettingsVersion,
  DEFAULT_SETTINGS,
} from "#/services/settings";
import { useSaveSettings } from "./mutation/use-save-settings";

/**
 * Get the settings from local storage.
 *
 * The only purpose of this function now is for the migration of settings.
 * @returns the settings from local storage
 * @deprecated
 */
const getLocalStorageSettings = () => {
  const llmModel = localStorage.getItem("LLM_MODEL");
  const baseUrl = localStorage.getItem("LLM_BASE_URL");
  const agent = localStorage.getItem("AGENT");
  const language = localStorage.getItem("LANGUAGE");
  const llmApiKey = localStorage.getItem("LLM_API_KEY");
  const confirmationMode = localStorage.getItem("CONFIRMATION_MODE") === "true";
  const securityAnalyzer = localStorage.getItem("SECURITY_ANALYZER");
  const enableDefaultCondenser =
    localStorage.getItem("ENABLE_DEFAULT_CONDENSER") === "true";

  return {
    LLM_MODEL: llmModel || DEFAULT_SETTINGS.LLM_MODEL,
    LLM_BASE_URL: baseUrl || DEFAULT_SETTINGS.LLM_BASE_URL,
    AGENT: agent || DEFAULT_SETTINGS.AGENT,
    LANGUAGE: language || DEFAULT_SETTINGS.LANGUAGE,
    LLM_API_KEY: llmApiKey || DEFAULT_SETTINGS.LLM_API_KEY,
    CONFIRMATION_MODE: confirmationMode || DEFAULT_SETTINGS.CONFIRMATION_MODE,
    SECURITY_ANALYZER: securityAnalyzer || DEFAULT_SETTINGS.SECURITY_ANALYZER,
    REMOTE_RUNTIME_RESOURCE_FACTOR:
      DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
    GITHUB_TOKEN_IS_SET: DEFAULT_SETTINGS.GITHUB_TOKEN_IS_SET,
    ENABLE_DEFAULT_CONDENSER:
      enableDefaultCondenser || DEFAULT_SETTINGS.ENABLE_DEFAULT_CONDENSER,
  };
};

const removeLocalStorageSettings = () => {
  localStorage.removeItem("LLM_MODEL");
  localStorage.removeItem("LLM_BASE_URL");
  localStorage.removeItem("AGENT");
  localStorage.removeItem("LANGUAGE");
  localStorage.removeItem("LLM_API_KEY");
  localStorage.removeItem("CONFIRMATION_MODE");
  localStorage.removeItem("SECURITY_ANALYZER");
  localStorage.removeItem("ENABLE_DEFAULT_CONDENSER");
};

// In this case, we may want to override a previous choice made by the user.
export const useMaybeMigrateSettings = () => {
  const { mutateAsync: saveSettings } = useSaveSettings();
  const { isUpToDate } = useCurrentSettings();

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

    if (currentVersion < 6) {
      removeLocalStorageSettings();
      // TODO: clear ghToken too?
    }
  };

  React.useEffect(() => {
    if (!isUpToDate) {
      maybeMigrateSettings();
    }
  }, []);
};
