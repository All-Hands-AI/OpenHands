import React from "react";
import BaseModal from "../BaseModal";
import SettingsForm from "./SettingsForm";
import {
  fetchAgents,
  fetchModels,
  getCurrentSettings,
  saveSettings,
} from "../../services/settingsService";

interface SettingsProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const SettingsModal: React.FC<SettingsProps> = ({ isOpen, onOpenChange }) => {
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

  const handleModelChange = (model: string) => {
    setSettings((prev) => ({ ...prev, LLM_MODEL: model }));
  };

  const handleAgentChange = (agent: string) => {
    setSettings((prev) => ({ ...prev, AGENT: agent }));
  };

  const handleLanguageChange = (language: string) => {
    setSettings((prev) => ({ ...prev, LANGUAGE: language }));
  };

  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title="Configuration"
      subtitle="Adjust settings to your liking"
      actions={[
        {
          label: "Save",
          action: () => {
            saveSettings(settings);
          },
          closeAfterAction: true,
          className: "bg-primary rounded-small",
        },
        {
          label: "Cancel",
          action: () => {},
          closeAfterAction: true,
          className: "bg-neutral-500 rounded-small",
        },
      ]}
    >
      <SettingsForm
        settings={settings}
        models={models}
        agents={agents}
        onModelChange={handleModelChange}
        onAgentChange={handleAgentChange}
        onLanguageChange={handleLanguageChange}
      />
    </BaseModal>
  );
};

export default SettingsModal;
