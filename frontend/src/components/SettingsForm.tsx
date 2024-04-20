import React from "react";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
} from "../services/settingsService";

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
      <span>{currentSettings.LLM_MODEL || models[0]}</span>
      <span>{currentSettings.AGENT || agents[0]}</span>
    </div>
  );
};

export default SettingsForm;
