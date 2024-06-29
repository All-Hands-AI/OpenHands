import React, { useState, useEffect } from "react";
import { Input, useDisclosure } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import { AvailableLanguages } from "../../../i18n";
import { I18nKey } from "../../../i18n/declaration";
import { AutocompleteCombobox } from "./AutocompleteCombobox";
import {
  Settings,
  getDefaultSettings,
  settingsAreUpToDate,
} from "#/services/settings";

const REQUIRED_SETTINGS = ["LLM_MODEL", "AGENT"];

interface SettingsFormProps {
  models: string[];
  agents: string[];
  settings: Settings;
  agentIsRunning: boolean;
  disabled: boolean;
  hasUnsavedChanges: boolean;
  onModelChange: (model: string) => void;
  onAgentChange: (agent: string) => void;
  onLanguageChange: (language: string) => void;
  onAPIKeyChange: (key: string) => void;
  onResetSettings: () => void;
  onSaveSettings: (newSettings: Settings) => void;
}

function SettingsForm({
  models,
  agents,
  settings,
  agentIsRunning,
  disabled,
  hasUnsavedChanges,
  onModelChange,
  onAgentChange,
  onLanguageChange,
  onAPIKeyChange,
  onResetSettings,
  onSaveSettings,
}: SettingsFormProps): JSX.Element {
  const { t } = useTranslation();
  const { isOpen: isVisible, onOpenChange: onVisibleChange } = useDisclosure();
  const [loading, setLoading] = useState(true);
  const isFormDisabled = disabled || agentIsRunning;
  const saveIsDisabled =
    disabled ||
    REQUIRED_SETTINGS.some((key) => !settings[key as keyof Settings]);

  useEffect(() => {
    // Load stored settings when component mounts
    const storedSettings = localStorage.getItem("settings");
    if (storedSettings) {
      const parsedSettings = JSON.parse(storedSettings);
      onModelChange(parsedSettings.LLM_MODEL || settings.LLM_MODEL);
      onAgentChange(parsedSettings.AGENT || settings.AGENT);
      onLanguageChange(parsedSettings.LANGUAGE || settings.LANGUAGE);
      onAPIKeyChange(parsedSettings.LLM_API_KEY || settings.LLM_API_KEY);
    }
    setLoading(false);
  }, []);

  const handleSave = () => {
    onSaveSettings(settings);
  };

  const handleReset = () => {
    onResetSettings();
    const defaultSettings = getDefaultSettings();
    onModelChange(defaultSettings.LLM_MODEL);
    onAgentChange(defaultSettings.AGENT);
    onLanguageChange(defaultSettings.LANGUAGE);
    onAPIKeyChange(defaultSettings.LLM_API_KEY);
  };

  let subtitle = t(I18nKey.CONFIGURATION$MODAL_SUB_TITLE);
  if (loading) {
    subtitle = t(I18nKey.CONFIGURATION$AGENT_LOADING);
  } else if (agentIsRunning) {
    subtitle = t(I18nKey.CONFIGURATION$AGENT_RUNNING);
  } else if (!settingsAreUpToDate()) {
    subtitle = t(I18nKey.CONFIGURATION$SETTINGS_NEED_UPDATE_MESSAGE);
  }

  return (
    <div className="space-y-4 text-foreground bg-background p-4 rounded-lg">
      <p className="mb-4 text-foreground">{subtitle}</p>
      <AutocompleteCombobox
        ariaLabel="agent"
        items={agents.map((agent) => ({ value: agent, label: agent }))}
        defaultKey={settings.AGENT}
        onChange={onAgentChange}
        tooltip={t(I18nKey.SETTINGS$AGENT_TOOLTIP)}
        disabled={isFormDisabled}
      />
      <AutocompleteCombobox
        ariaLabel="model"
        items={models.map((model) => ({ value: model, label: model }))}
        defaultKey={settings.LLM_MODEL}
        onChange={(e) => {
          onModelChange(e);
        }}
        tooltip={t(I18nKey.SETTINGS$MODEL_TOOLTIP)}
        allowCustomValue
        disabled={isFormDisabled}
      />
      <Input
        label="API Key"
        isDisabled={isFormDisabled}
        aria-label="apikey"
        data-testid="apikey"
        placeholder={t(I18nKey.SETTINGS$API_KEY_PLACEHOLDER)}
        type={isVisible ? "text" : "password"}
        value={settings.LLM_API_KEY || ""}
        onChange={(e) => {
          onAPIKeyChange(e.target.value);
        }}
        className="bg-bg-input border-border"
        endContent={
          <button
            className="focus:outline-none"
            type="button"
            onClick={onVisibleChange}
            disabled={isFormDisabled}
          >
            {isVisible ? (
              <FaEye className="text-2xl text-default-400 pointer-events-none" />
            ) : (
              <FaEyeSlash className="text-2xl text-default-400 pointer-events-none" />
            )}
          </button>
        }
      />
      <AutocompleteCombobox
        ariaLabel="language"
        items={AvailableLanguages}
        defaultKey={settings.LANGUAGE}
        onChange={onLanguageChange}
        tooltip={t(I18nKey.SETTINGS$LANGUAGE_TOOLTIP)}
        disabled={isFormDisabled}
      />
      {hasUnsavedChanges && (
        <div className="unsaved-changes-warning text-accent">
          {t(I18nKey.CONFIGURATION$UNSAVED_CHANGES)}
        </div>
      )}
      <div className="flex justify-center space-x-4">
        <button
          type="button"
          className="px-4 py-2 bg-red-500 text-white hover:bg-red-600 rounded"
          onClick={handleReset}
          disabled={isFormDisabled} // Disable if agent is running
        >
          {t(I18nKey.CONFIGURATION$MODAL_RESET_BUTTON_LABEL)}
        </button>
        <button
          type="button"
          className="px-4 py-2 bg-blue-500 text-primary-foreground hover:opacity-80 rounded"
          onClick={handleSave}
          disabled={saveIsDisabled || isFormDisabled}
        >
          {t(I18nKey.CONFIGURATION$MODAL_SAVE_BUTTON_LABEL)}
        </button>
      </div>
    </div>
  );
}

export default SettingsForm;
