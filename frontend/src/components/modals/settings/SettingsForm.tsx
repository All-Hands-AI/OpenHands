import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { AvailableLanguages } from "../../../i18n";
import { I18nKey } from "../../../i18n/declaration";
import { RootState } from "../../../store";
import AgentTaskState from "../../../types/AgentTaskState";
import { AutocompleteCombobox } from "./AutocompleteCombobox";

interface SettingsFormProps {
  settings: Partial<Settings>;
  models: string[];
  agents: string[];

  onModelChange: (model: string) => void;
  onAgentChange: (agent: string) => void;
  onLanguageChange: (language: string) => void;
}

function SettingsForm({
  settings,
  models,
  agents,
  onModelChange,
  onAgentChange,
  onLanguageChange,
}: SettingsFormProps) {
  const { t } = useTranslation();
  const { curTaskState } = useSelector((state: RootState) => state.agent);
  const [disabled, setDisabled] = React.useState<boolean>(false);

  useEffect(() => {
    if (
      curTaskState === AgentTaskState.RUNNING ||
      curTaskState === AgentTaskState.PAUSED
    ) {
      setDisabled(true);
    } else {
      setDisabled(false);
    }
  }, [curTaskState, setDisabled]);

  return (
    <>
      <AutocompleteCombobox
        ariaLabel="model"
        items={models.map((model) => ({ value: model, label: model }))}
        defaultKey={settings.LLM_MODEL || models[0]}
        onChange={onModelChange}
        tooltip={t(I18nKey.SETTINGS$MODEL_TOOLTIP)}
        allowCustomValue // user can type in a custom LLM model that is not in the list
        disabled={disabled}
      />
      <AutocompleteCombobox
        ariaLabel="agent"
        items={agents.map((agent) => ({ value: agent, label: agent }))}
        defaultKey={settings.AGENT || agents[0]}
        onChange={onAgentChange}
        tooltip={t(I18nKey.SETTINGS$AGENT_TOOLTIP)}
        disabled={disabled}
      />
      <AutocompleteCombobox
        ariaLabel="language"
        items={AvailableLanguages}
        defaultKey={settings.LANGUAGE || "en"}
        onChange={onLanguageChange}
        tooltip={t(I18nKey.SETTINGS$LANGUAGE_TOOLTIP)}
        disabled={disabled}
      />
    </>
  );
}

export default SettingsForm;
