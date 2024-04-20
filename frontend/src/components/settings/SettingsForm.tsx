import React from "react";
import { Select, SelectItem } from "@nextui-org/react";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
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
        <AutocompleteCombobox
          ariaLabel="model"
          items={models.map((model) => ({ value: model, label: model }))}
          defaultKey={currentSettings.LLM_MODEL || models[0]}
        />
      )}
      {agents.length > 0 && (
        <AutocompleteCombobox
          ariaLabel="agent"
          items={agents.map((agent) => ({ value: agent, label: agent }))}
          defaultKey={currentSettings.AGENT || agents[0]}
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
    </div>
  );
};

export default SettingsForm;
