import { Input, Switch, Tooltip, useDisclosure } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import { AvailableLanguages } from "../../../i18n";
import { I18nKey } from "../../../i18n/declaration";
import { AutocompleteCombobox } from "./AutocompleteCombobox";
import { Settings } from "#/services/settings";
import { organizeModelsAndProviders } from "#/utils/organizeModelsAndProviders";
import { ModelSelector } from "./ModelSelector";

interface SettingsFormProps {
  settings: Settings;
  models: string[];
  agents: string[];
  securityAnalyzers: string[];
  disabled: boolean;

  onModelChange: (model: string) => void;
  onBaseURLChange: (baseURL: string) => void;
  onAPIKeyChange: (apiKey: string) => void;
  onAgentChange: (agent: string) => void;
  onLanguageChange: (language: string) => void;
  onConfirmationModeChange: (confirmationMode: boolean) => void;
  onSecurityAnalyzerChange: (securityAnalyzer: string) => void;
}

function SettingsForm({
  settings,
  models,
  agents,
  securityAnalyzers,
  disabled,
  onModelChange,
  onBaseURLChange,
  onAPIKeyChange,
  onAgentChange,
  onLanguageChange,
  onConfirmationModeChange,
  onSecurityAnalyzerChange,
}: SettingsFormProps) {
  const { t } = useTranslation();
  const { isOpen: isVisible, onOpenChange: onVisibleChange } = useDisclosure();
  const advancedAlreadyInUse = React.useMemo(
    () =>
      !!settings.SECURITY_ANALYZER ||
      !!settings.CONFIRMATION_MODE ||
      !!settings.LLM_BASE_URL ||
      (!!settings.LLM_MODEL && !models.includes(settings.LLM_MODEL)),
    [],
  );
  const [enableAdvanced, setEnableAdvanced] =
    React.useState(advancedAlreadyInUse);

  return (
    <>
      <Switch
        data-testid="advanced-options-toggle"
        aria-checked={enableAdvanced}
        isSelected={enableAdvanced}
        onValueChange={(value) => setEnableAdvanced(value)}
      >
        Advanced Options
      </Switch>
      {enableAdvanced && (
        <>
          <Input
            data-testid="custom-model-input"
            label="Custom Model"
            onValueChange={onModelChange}
            defaultValue={settings.LLM_MODEL}
          />
          <Input
            data-testid="base-url-input"
            label="Base URL"
            onValueChange={onBaseURLChange}
            defaultValue={settings.LLM_BASE_URL}
          />
        </>
      )}
      {!enableAdvanced && (
        <ModelSelector
          isDisabled={disabled}
          models={organizeModelsAndProviders(models)}
          onModelChange={onModelChange}
          defaultModel={settings.LLM_MODEL}
        />
      )}
      <Input
        label="API Key"
        isDisabled={disabled}
        aria-label="apikey"
        data-testid="apikey"
        placeholder={t(I18nKey.SETTINGS$API_KEY_PLACEHOLDER)}
        type={isVisible ? "text" : "password"}
        value={settings.LLM_API_KEY || ""}
        onChange={(e) => {
          onAPIKeyChange(e.target.value);
        }}
        endContent={
          <button
            className="focus:outline-none"
            type="button"
            onClick={onVisibleChange}
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
        disabled={disabled}
      />
      {enableAdvanced && (
        <AutocompleteCombobox
          ariaLabel="agent"
          items={agents.map((agent) => ({ value: agent, label: agent }))}
          defaultKey={settings.AGENT}
          onChange={onAgentChange}
          tooltip={t(I18nKey.SETTINGS$AGENT_TOOLTIP)}
        />
      )}
      {enableAdvanced && (
        <AutocompleteCombobox
          ariaLabel="securityanalyzer"
          items={securityAnalyzers.map((securityAnalyzer) => ({
            value: securityAnalyzer,
            label: securityAnalyzer,
          }))}
          defaultKey={settings.SECURITY_ANALYZER}
          onChange={onSecurityAnalyzerChange}
          tooltip={t(I18nKey.SETTINGS$SECURITY_ANALYZER)}
          disabled={disabled}
        />
      )}
      {enableAdvanced && (
        <Switch
          aria-label="confirmationmode"
          data-testid="confirmationmode"
          defaultSelected={
            settings.CONFIRMATION_MODE || !!settings.SECURITY_ANALYZER
          }
          onValueChange={onConfirmationModeChange}
          isDisabled={disabled || !!settings.SECURITY_ANALYZER}
          isSelected={settings.CONFIRMATION_MODE}
        >
          <Tooltip
            content={t(I18nKey.SETTINGS$CONFIRMATION_MODE_TOOLTIP)}
            closeDelay={100}
            delay={500}
          >
            {t(I18nKey.SETTINGS$CONFIRMATION_MODE)}
          </Tooltip>
        </Switch>
      )}
    </>
  );
}

export default SettingsForm;
