import React from "react";
import {
  Autocomplete,
  AutocompleteItem,
  Select,
  SelectItem,
} from "@nextui-org/react";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
} from "../services/settingsService";
import { AvailableLanguages } from "../i18n";

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

  return (
    <div>
      {models.length > 0 && (
        <Autocomplete
          aria-label="model"
          defaultItems={models.map((model) => ({ value: model, label: model }))}
          defaultSelectedKey={currentSettings.LLM_MODEL || models[0]}
        >
          {(model) => (
            <AutocompleteItem key={model.value}>{model.label}</AutocompleteItem>
          )}
        </Autocomplete>
      )}
      {agents.length > 0 && (
        <Autocomplete
          aria-label="agent"
          defaultItems={agents.map((agent) => ({ value: agent, label: agent }))}
          defaultSelectedKey={currentSettings.AGENT || agents[0]}
        >
          {(agent) => (
            <AutocompleteItem key={agent.value}>{agent.label}</AutocompleteItem>
          )}
        </Autocomplete>
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
    </div>
  );
};

export default SettingsForm;
