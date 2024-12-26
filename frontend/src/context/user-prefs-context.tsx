import React from "react";
import posthog from "posthog-js";
import {
  getSettings,
  saveSettings as updateAndSaveSettingsToBackend,
  settingsAreUpToDate as checkIfSettingsAreUpToDate,
  DEFAULT_SETTINGS,
} from "#/services/settings";
import { Settings } from "#/api/open-hands.types";

interface UserPrefsContextType {
  settings: Settings;
  settingsAreUpToDate: boolean;
  saveSettings: (settings: Partial<Settings>) => void;
}

const UserPrefsContext = React.createContext<UserPrefsContextType | undefined>(
  undefined,
);

function UserPrefsProvider({ children }: React.PropsWithChildren) {
  const [settings, setSettings] = React.useState<Settings>(DEFAULT_SETTINGS);
  const [settingsAreUpToDate, setSettingsAreUpToDate] = React.useState(
    checkIfSettingsAreUpToDate(),
  );

  const saveSettings = async (newSettings: Partial<Settings>) => {
    updateAndSaveSettingsToBackend(newSettings);
    const retrievedSettings = await getSettings();
    setSettings(retrievedSettings);
    setSettingsAreUpToDate(checkIfSettingsAreUpToDate());
  };

  React.useEffect(() => {
    const fetchSettings = async () => {
      const initialSettings = await getSettings();
      setSettings(initialSettings);
      setSettingsAreUpToDate(checkIfSettingsAreUpToDate());
    };

    fetchSettings();
  }, []);

  React.useEffect(() => {
    if (settings.LLM_API_KEY) {
      posthog.capture("user_activated");
    }
  }, [settings.LLM_API_KEY]);

  const value = React.useMemo(
    () => ({
      settings,
      settingsAreUpToDate,
      saveSettings,
    }),
    [settings, settingsAreUpToDate],
  );

  return (
    <UserPrefsContext.Provider value={value}>
      {children}
    </UserPrefsContext.Provider>
  );
}

function useUserPrefs() {
  const context = React.useContext(UserPrefsContext);
  if (context === undefined) {
    throw new Error("useUserPrefs must be used within a UserPrefsProvider");
  }
  return context;
}

export { UserPrefsProvider, useUserPrefs };
