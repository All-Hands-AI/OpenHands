import React from "react";
import {
  LATEST_SETTINGS_VERSION,
  Settings,
  settingsAreUpToDate,
} from "#/services/settings";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";

interface SettingsContextType {
  isUpToDate: boolean;
  setIsUpToDate: (value: boolean) => void;
  saveUserSettings: (newSettings: Partial<Settings>) => Promise<void>;
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

  const [isUpToDate, setIsUpToDate] = React.useState(settingsAreUpToDate());

  const saveUserSettings = async (newSettings: Partial<Settings>) => {
    const updatedSettings: Partial<Settings> = {
      ...userSettings,
      ...newSettings,
    };
    await saveSettings(updatedSettings, {
      onSuccess: () => {
        if (!isUpToDate) {
          localStorage.setItem(
            "SETTINGS_VERSION",
            LATEST_SETTINGS_VERSION.toString(),
          );
          setIsUpToDate(true);
        }
      },
    });
  };

  const value = React.useMemo(
    () => ({
      isUpToDate,
      setIsUpToDate,
      saveUserSettings,
      settings: userSettings,
    }),
    [isUpToDate, setIsUpToDate, saveUserSettings, userSettings],
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
