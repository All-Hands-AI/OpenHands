import React from "react";
const LATEST_SETTINGS_VERSION = 5;

export const getCurrentSettingsVersion = () => {
  const settingsVersion = localStorage.getItem("SETTINGS_VERSION");
  if (!settingsVersion) return 0;
  try {
    return parseInt(settingsVersion, 10);
  } catch (e) {
    return 0;
  }
};

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
    <SettingsUpToDateContext.Provider value={value}>{children}</SettingsUpToDateContext.Provider>
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
