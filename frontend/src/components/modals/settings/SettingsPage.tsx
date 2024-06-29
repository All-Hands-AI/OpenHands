import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import SettingsForm from "./SettingsForm";
import { Settings } from "#/services/settings";
import { Theme } from "#/utils/themeUtils";
import ThemeSelector from "./ThemeSelector";

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

  const handleReset = () => {
    onModelChange(initialSettings.LLM_MODEL);
    onAgentChange(initialSettings.AGENT);
    onLanguageChange(initialSettings.LANGUAGE);
    onAPIKeyChange(initialSettings.LLM_API_KEY);
    onThemeChange(initialSettings.THEME as "light" | "dark");
  };

  const handleSave = () => {
    onSaveSettings(settings); // Directly call onSaveSettings with the current settings
  };

  const handleThemeChange = (newTheme: Theme) => {
    onThemeChange(newTheme);
    onSaveSettings({ ...settings, THEME: newTheme });
  };

  return (
    <div
      className={`absolute inset-0 bg-neutral-800 text-white overflow-hidden ${
        isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      <div className="h-full flex flex-col overflow-hidden">
        <div className="flex-grow overflow-y-auto p-4 space-y-4 px-[20%]">
          <div className="bg-neutral-700 p-4 rounded-lg border border-blue-400 shadow-md shadow-blue-400/20">
            <h1 className="text-xl font-bold mb-2 text-foreground">
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
              onLanguageChange={onLanguageChange}
              onAPIKeyChange={onAPIKeyChange}
              onResetSettings={handleReset}
              onSaveSettings={handleSave}
              onError={onError}
              hasUnsavedChanges={hasUnsavedChanges}
            />
          </div>
          <div className="bg-neutral-700 p-4 rounded-lg border border-blue-400 shadow-md shadow-blue-400/20">
            <h2 className="text-lg font-bold mb-2 text-foreground">
              {t(I18nKey.CONFIGURATION$THEME_LABEL)}
            </h2>
            <ThemeSelector
              theme={theme}
              onThemeChange={handleThemeChange}
              disabled={disabled}
            />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-neutral-700 flex justify-center">
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
