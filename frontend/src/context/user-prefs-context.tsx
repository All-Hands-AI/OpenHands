import React from "react";
import posthog from "posthog-js";
import {
  getSettings,
  Settings,
  saveSettings as updateAndSaveSettingsToLocalStorage,
  settingsAreUpToDate as checkIfSettingsAreUpToDate,
} from "#/services/settings";

interface UserPrefsContextType {
  settings: Settings;
  settingsAreUpToDate: boolean;
  saveSettings: (settings: Partial<Settings>) => void;
}

const UserPrefsContext = React.createContext<UserPrefsContextType | undefined>(
  undefined,
);

function UserPrefsProvider({ children }: React.PropsWithChildren) {
  const [settings, setSettings] = React.useState(getSettings());
  const [settingsAreUpToDate, setSettingsAreUpToDate] = React.useState(
    checkIfSettingsAreUpToDate(),
  );

  const saveSettings = (newSettings: Partial<Settings>) => {
    updateAndSaveSettingsToLocalStorage(newSettings);
    setSettings(getSettings());
    setSettingsAreUpToDate(checkIfSettingsAreUpToDate());
  };

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
