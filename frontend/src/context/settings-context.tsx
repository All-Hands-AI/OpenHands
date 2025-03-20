import React from "react";
import { MutateOptions } from "@tanstack/react-query";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { PostSettings, Settings } from "#/types/settings";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

type SaveUserSettingsConfig = {
  onSuccess: MutateOptions<void, Error, Partial<PostSettings>>["onSuccess"];
};

interface SettingsContextType {
  saveUserSettings: (
    newSettings: Partial<PostSettings>,
    config?: SaveUserSettingsConfig,
  ) => Promise<void>;
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

  const saveUserSettings = async (
    newSettings: Partial<PostSettings>,
    config?: SaveUserSettingsConfig,
  ) => {
    const updatedSettings: Partial<PostSettings> = {
      ...userSettings,
      ...newSettings,
    };

    if (updatedSettings.LLM_API_KEY === "**********") {
      delete updatedSettings.LLM_API_KEY;
    }

    await saveSettings(updatedSettings, {
      onSuccess: config?.onSuccess,
      onError: (error) => {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage);
      },
    });
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
