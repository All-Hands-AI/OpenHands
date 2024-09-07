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
  onCustomModelChange: (model: string) => void;
  onModelTypeChange: (type: "custom" | "default") => void;
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
  onCustomModelChange,
  onModelTypeChange,
  onAPIKeyChange,
  onAgentChange,
  onLanguageChange,
  onConfirmationModeChange,
  onSecurityAnalyzerChange,
}: SettingsFormProps) {
  const { t } = useTranslation();
  const { isOpen: isVisible, onOpenChange: onVisibleChange } = useDisclosure();
  const [isAgentSelectEnabled, setIsAgentSelectEnabled] = React.useState(false);
  const [usingCustomModel, setUsingCustomModel] = React.useState(
    settings.USING_CUSTOM_MODEL,
  );

  const changeModelType = (type: "custom" | "default") => {
    if (type === "custom") {
      setUsingCustomModel(true);
      onModelTypeChange("custom");
    } else {
      setUsingCustomModel(false);
      onModelTypeChange("default");
    }
  };

  return (
    <>
      <Switch
        data-testid="custom-model-toggle"
        aria-checked={usingCustomModel}
        isSelected={usingCustomModel}
        onValueChange={(value) => changeModelType(value ? "custom" : "default")}
      >
        Use custom model
      </Switch>
      {usingCustomModel && (
        <Input
          data-testid="custom-model-input"
          label="Custom Model"
          onValueChange={onCustomModelChange}
          defaultValue={settings.CUSTOM_LLM_MODEL}
        />
      )}
      {!usingCustomModel && (
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
      <AutocompleteCombobox
        ariaLabel="agent"
        items={agents.map((agent) => ({ value: agent, label: agent }))}
        defaultKey={settings.AGENT}
        onChange={onAgentChange}
        tooltip={t(I18nKey.SETTINGS$AGENT_TOOLTIP)}
        disabled={disabled || !isAgentSelectEnabled}
      />
      <Switch
        defaultSelected={false}
        isSelected={isAgentSelectEnabled}
        onValueChange={setIsAgentSelectEnabled}
        aria-label="enableagentselect"
        data-testid="enableagentselect"
      >
        {t(I18nKey.SETTINGS$AGENT_SELECT_ENABLED)}
      </Switch>
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
    </>
  );
}

export default SettingsForm;
