import React from "react";
import { Select, SelectItem } from "@nextui-org/react";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
  saveSettings,
} from "../../services/settingsService";
import { AvailableLanguages } from "../../i18n";
import { AutocompleteCombobox } from "./AutocompleteCombobox";
import { isDifferent } from "./utils";

type Settings = {
  LLM_MODEL: string;
  AGENT: string;
  LANGUAGE: string;
};

interface SettingsFormProps {}

const SettingsForm: React.FC<SettingsFormProps> = () => {
  const [models, setModels] = React.useState<string[]>([]);
  const [agents, setAgents] = React.useState<string[]>([]);

  const [currentSettings, setCurrentSettings] = React.useState<
    Partial<Settings>
  >({});
  const [newSettings, setNewSettings] = React.useState<Partial<Settings>>({});

  React.useEffect(() => {
    const settings = getCurrentSettings();
    setCurrentSettings(settings);
  }, []);

  React.useEffect(() => {
    (async () => {
      const fetchedModels = await fetchModels();
      setModels(fetchedModels);

      const fetchedAgents = await fetchAgents();
      setAgents(fetchedAgents);
    })();
  }, []);

  const onSave = () => {
    saveSettings(newSettings);
  };

  return (
    <div>
      {models.length > 0 && (
        <AutocompleteCombobox
          ariaLabel="model"
          items={models.map((model) => ({ value: model, label: model }))}
          defaultKey={currentSettings.LLM_MODEL || models[0]}
          onChange={(key) => setNewSettings({ ...newSettings, LLM_MODEL: key })}
        />
      )}
      {agents.length > 0 && (
        <AutocompleteCombobox
          ariaLabel="agent"
          items={agents.map((agent) => ({ value: agent, label: agent }))}
          defaultKey={currentSettings.AGENT || agents[0]}
          onChange={(key) => setNewSettings({ ...newSettings, AGENT: key })}
        />
      )}
      <Select
        aria-label="language"
        defaultSelectedKeys={[currentSettings.LANGUAGE || "en"]}
      >
        {AvailableLanguages.map((language) => (
          <SelectItem key={language.value} value={language.value}>
            {language.label}
          </SelectItem>
        ))}
      </Select>

      <button
        data-testid="save"
        type="button"
        disabled={!isDifferent(currentSettings, newSettings)}
        onClick={onSave}
      >
        Save
      </button>
    </div>
  );
};

export default SettingsForm;
