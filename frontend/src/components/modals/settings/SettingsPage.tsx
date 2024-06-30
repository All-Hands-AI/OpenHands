import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import SettingsForm from "./SettingsForm";
import { Settings } from "#/services/settings";
import { Theme } from "#/utils/themeUtils";
import ThemeSelector from "./ThemeSelector";
import { AutocompleteCombobox } from "./AutocompleteCombobox";
import { AvailableLanguages } from "#/i18n";

interface SettingsPageProps {
  isOpen: boolean;
  onClose: () => void; // Add this line
  models: string[];
  agents: string[];
  settings: Settings;
  agentIsRunning: boolean;
  disabled: boolean;
  theme: Theme;
  onModelChange: (model: string) => void;
  onAgentChange: (agent: string) => void;
  onLanguageChange: (language: string) => void;
  onAPIKeyChange: (key: string) => void;
  onSaveSettings: (newSettings: Settings) => void;
  onResetSettings: () => void;
  onError: (error: Error, isCritical?: boolean) => void;
  onThemeChange: (theme: Theme) => void;
}

function SettingsPage({
  isOpen,
  onClose,
  models,
  agents,
  settings,
  agentIsRunning,
  disabled,
  theme,
  onModelChange,
  onAgentChange,
  onLanguageChange,
  onAPIKeyChange,
  onSaveSettings,
  onResetSettings,
  onError,
  onThemeChange,
}: SettingsPageProps): JSX.Element {
  const { t } = useTranslation();
  const [initialSettings, setInitialSettings] = useState<Settings>(settings);

  useEffect(() => {
    setInitialSettings(settings);
  }, [settings]);

  const hasUnsavedChanges =
    JSON.stringify(settings) !== JSON.stringify(initialSettings);

  const handleError = (error: Error) => {
    onError(error, false);
  };

  const handleSave = () => {
    onSaveSettings(settings); // Directly call onSaveSettings with the current settings
  };

  const handleLanguageChange = (language: string) => {
    onLanguageChange(language);
  };

  const handleThemeChange = (newTheme: Theme) => {
    onThemeChange(newTheme);
    onSaveSettings({ ...settings, THEME: newTheme });
  };

  return (
    <div
      className={`absolute inset-0 bg-bg-light dark:bg-bg-dark text-foreground overflow-hidden transition-opacity duration-300 ${
        isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      <div className="h-full flex flex-col overflow-hidden">
        <div className="flex-grow overflow-y-auto p-4 space-y-4 px-[20%]">
          <div className="dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-md">
            <h1 className="text-xl font-bold mb-2 text-gray-800 dark:text-gray-200">
              {t(I18nKey.CONFIGURATION$MODAL_TITLE)}
            </h1>
            <SettingsForm
              models={models}
              agents={agents}
              settings={settings}
              agentIsRunning={agentIsRunning}
              disabled={disabled}
              onModelChange={onModelChange}
              onAgentChange={onAgentChange}
              onAPIKeyChange={onAPIKeyChange}
              onSaveSettings={handleSave}
              onResetSettings={onResetSettings}
              hasUnsavedChanges={hasUnsavedChanges}
              onError={handleError}
            />
          </div>
          <div className="dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-md">
            <h2 className="text-lg font-bold mb-2 text-gray-800 dark:text-gray-200">
              {t(I18nKey.CONFIGURATION$LANGUAGE_SELECT_LABEL)}
            </h2>
            <AutocompleteCombobox
              ariaLabel="language"
              items={AvailableLanguages}
              defaultKey={settings.LANGUAGE}
              onChange={handleLanguageChange}
              tooltip={t(I18nKey.SETTINGS$LANGUAGE_TOOLTIP)}
              disabled={disabled}
            />
          </div>
          <div className="dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-md">
            <h2 className="text-lg font-bold mb-2 text-gray-800 dark:text-gray-200">
              {t(I18nKey.CONFIGURATION$THEME_LABEL)}
            </h2>
            <ThemeSelector
              theme={theme}
              onThemeChange={handleThemeChange}
              disabled={disabled}
            />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-center">
          <button
            onClick={onClose}
            type="button"
            className="px-4 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors font-medium text-sm"
          >
            {t(I18nKey.CONFIGURATION$MODAL_CLOSE_BUTTON_LABEL)}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
