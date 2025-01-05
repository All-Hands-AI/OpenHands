import React from "react";
import {
  LATEST_SETTINGS_VERSION,
  getCurrentSettingsVersion,
} from "#/services/settings";

export const settingsAreUpToDate = () =>
  getCurrentSettingsVersion() === LATEST_SETTINGS_VERSION;

interface SettingsUpToDateContextType {
  isUpToDate: boolean;
  setIsUpToDate: (value: boolean) => void;
}

const SettingsUpToDateContext = React.createContext<
  SettingsUpToDateContextType | undefined
>(undefined);

interface SettingsUpToDateProviderProps {
  children: React.ReactNode;
}

export function SettingsUpToDateProvider({
  children,
}: SettingsUpToDateProviderProps) {
  const [isUpToDate, setIsUpToDate] = React.useState(settingsAreUpToDate());

  const value = React.useMemo(
    () => ({ isUpToDate, setIsUpToDate }),
    [isUpToDate, setIsUpToDate],
  );

  return (
    <SettingsUpToDateContext.Provider value={value}>
      {children}
    </SettingsUpToDateContext.Provider>
  );
}

export function useSettingsUpToDate() {
  const context = React.useContext(SettingsUpToDateContext);
  if (context === undefined) {
    throw new Error(
      "useSettingsUpToDate must be used within a SettingsUpToDateProvider",
    );
  }
  return context;
}
