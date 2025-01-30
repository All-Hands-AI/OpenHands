import React from "react";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { PostSettings, Settings } from "#/types/settings";

interface SettingsContextType {
  saveUserSettings: (newSettings: Partial<PostSettings>) => Promise<void>;
  settings: Settings | undefined;
}

const SettingsContext = React.createContext<SettingsContextType | undefined>(
  undefined,
);

interface SettingsProviderProps {
  children: React.ReactNode;
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const { data: userSettings } = useSettings();
  const { mutateAsync: saveSettings } = useSaveSettings();

  const saveUserSettings = async (newSettings: Partial<PostSettings>) => {
    const updatedSettings: Partial<PostSettings> = {
      ...userSettings,
      ...newSettings,
    };

    if (updatedSettings.LLM_API_KEY === "**********") {
      delete updatedSettings.LLM_API_KEY;
    }

    await saveSettings(updatedSettings);
  };

  const value = React.useMemo(
    () => ({
      saveUserSettings,
      settings: userSettings,
    }),
    [saveUserSettings, userSettings],
  );

  return <SettingsContext value={value}>{children}</SettingsContext>;
}

export function useCurrentSettings() {
  const context = React.useContext(SettingsContext);
  if (context === undefined) {
    throw new Error(
      "useCurrentSettings must be used within a SettingsProvider",
    );
  }
  return context;
}
