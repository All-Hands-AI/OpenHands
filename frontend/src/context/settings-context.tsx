import React from "react";
import posthog from "posthog-js";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getSettings,
  Settings,
  saveSettings,
  settingsAreUpToDate as checkIfSettingsAreUpToDate,
  DEFAULT_SETTINGS,
} from "#/services/settings";

interface SettingsContextType {
  settings: Settings;
  settingsAreUpToDate: boolean;
  saveSettings: (settings: Partial<Settings>) => void;
}

const SettingsContext = React.createContext<SettingsContextType | undefined>(
  undefined,
);

const SETTINGS_QUERY_KEY = ["settings"];

function SettingsProvider({ children }: React.PropsWithChildren) {
  const { data: settings } = useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: getSettings,
    initialData: DEFAULT_SETTINGS,
  });

  const [settingsAreUpToDate, setSettingsAreUpToDate] = React.useState(
    checkIfSettingsAreUpToDate(),
  );
  const queryClient = useQueryClient();

  const handleSaveSettings = async (newSettings: Partial<Settings>) => {
    await saveSettings(newSettings);
    queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    setSettingsAreUpToDate(checkIfSettingsAreUpToDate());
  };

  React.useEffect(() => {
    if (settings?.LLM_API_KEY) {
      posthog.capture("user_activated");
    }
  }, [settings?.LLM_API_KEY]);

  const value = React.useMemo(
    () => ({
      settings,
      settingsAreUpToDate,
      handleSaveSettings,
    }),
    [settings, settingsAreUpToDate],
  );

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

function useSettings() {
  const context = React.useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}

export { SettingsProvider, useSettings };
