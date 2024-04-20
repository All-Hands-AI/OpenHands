import React from "react";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
  saveSettings,
} from "../../services/settingsService";
import { AvailableLanguages } from "../../i18n";
import { AutocompleteCombobox } from "./AutocompleteCombobox";

type Settings = {
  LLM_MODEL: string;
  AGENT: string;
  LANGUAGE: string;
};

interface SettingsFormProps {}

const SettingsForm: React.FC<SettingsFormProps> = () => {
  const [models, setModels] = React.useState<string[]>([]);
  const [agents, setAgents] = React.useState<string[]>([]);

  const [settings, setSettings] =
    React.useState<Partial<Settings>>(getCurrentSettings());

  React.useEffect(() => {
    (async () => {
      setModels(await fetchModels());
      setAgents(await fetchAgents());
    })();
  }, []);

  return (
    <div>
      {models.length > 0 && (
        <AutocompleteCombobox
          ariaLabel="model"
          items={models.map((model) => ({ value: model, label: model }))}
          defaultKey={settings.LLM_MODEL || models[0]}
          onChange={(key) =>
            setSettings((prev) => ({ ...prev, LLM_MODEL: key }))
          }
        />
      )}
      {agents.length > 0 && (
        <AutocompleteCombobox
          ariaLabel="agent"
          items={agents.map((agent) => ({ value: agent, label: agent }))}
          defaultKey={settings.AGENT || agents[0]}
          onChange={(key) => setSettings((prev) => ({ ...prev, AGENT: key }))}
        />
      )}
      <AutocompleteCombobox
        ariaLabel="language"
        items={AvailableLanguages}
        defaultKey={settings.LANGUAGE || "en"}
        onChange={(key) => setSettings((prev) => ({ ...prev, LANGUAGE: key }))}
      />

      <button
        data-testid="save"
        type="button"
        onClick={() => saveSettings(settings)}
      >
        Save
      </button>
    </div>
  );
};

export default SettingsForm;
