import React from "react";
import { AvailableLanguages } from "src/i18n";
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
  return (
    <>
      <AutocompleteCombobox
        ariaLabel="model"
        items={models.map((model) => ({ value: model, label: model }))}
        defaultKey={settings.LLM_MODEL || models[0]}
        onChange={onModelChange}
        allowCustomValue // user can type in a custom LLM model that is not in the list
      />
      <AutocompleteCombobox
        ariaLabel="agent"
        items={agents.map((agent) => ({ value: agent, label: agent }))}
        defaultKey={settings.AGENT || agents[0]}
        onChange={onAgentChange}
      />
      <AutocompleteCombobox
        ariaLabel="language"
        items={AvailableLanguages}
        defaultKey={settings.LANGUAGE || "en"}
        onChange={onLanguageChange}
      />
    </>
  );
}

export default SettingsForm;
