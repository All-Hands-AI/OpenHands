import { Spinner } from "@nextui-org/react";
import i18next from "i18next";
import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { fetchAgents, fetchModels } from "#/api";
import { AvailableLanguages } from "#/i18n";
import { I18nKey } from "#/i18n/declaration";
import { initializeAgent } from "#/services/agent";
import AgentTaskState from "../../../types/AgentTaskState";
import {
  Settings,
  getSettings,
  getSettingsDifference,
  settingsAreUpToDate,
  maybeMigrateSettings,
  saveSettings,
} from "#/services/settings";
import toast from "#/utils/toast";
import BaseModal from "../base-modal/BaseModal";
import SettingsForm from "./SettingsForm";

interface SettingsProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function SettingsModal({ isOpen, onOpenChange }: SettingsProps) {
  const { t } = useTranslation();
  maybeMigrateSettings();
  const currentSettings = getSettings();

  const [models, setModels] = React.useState<string[]>([]);
  const [agents, setAgents] = React.useState<string[]>([]);
  const [settings, setSettings] = React.useState<Settings>(currentSettings);
  const [agentIsRunning, setAgentIsRunning] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState(true);
  const { curTaskState } = useSelector((state: RootState) => state.agent);

  useEffect(() => {
    setAgentIsRunning(
      curTaskState === AgentTaskState.RUNNING ||
      curTaskState === AgentTaskState.PAUSED ||
      curTaskState === AgentTaskState.AWAITING_USER_INPUT
    )
  }, [curTaskState]);


  React.useEffect(() => {
    (async () => {
      try {
        setModels(await fetchModels());
        setAgents(await fetchAgents());
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleModelChange = (model: string) => {
    // Needs to also reset the API key.
    const key = localStorage.getItem(`API_KEY_${model}`);
    setSettings((prev) => ({
      ...prev,
      LLM_MODEL: model,
      LLM_API_KEY: key || "",
    }));
  };

  const handleAgentChange = (agent: string) => {
    setSettings((prev) => ({ ...prev, AGENT: agent }));
  };

  const handleLanguageChange = (language: string) => {
    const key = AvailableLanguages.find(
      (lang) => lang.label === language,
    )?.value;

    if (key) setSettings((prev) => ({ ...prev, LANGUAGE: key }));
  };

  const handleAPIKeyChange = (key: string) => {
    setSettings((prev) => ({ ...prev, LLM_API_KEY: key }));
  };

  const handleSaveSettings = () => {
    const updatedSettings = getSettingsDifference(settings);
    saveSettings(settings);
    i18next.changeLanguage(settings.LANGUAGE);
    initializeAgent(settings); // reinitialize the agent with the new settings

    const sensitiveKeys = ["LLM_API_KEY"];

    Object.entries(updatedSettings).forEach(([key, value]) => {
      if (!sensitiveKeys.includes(key)) {
        toast.settingsChanged(`${key} set to "${value}"`);
      } else {
        toast.settingsChanged(`${key} has been updated securely.`);
      }
    });

    localStorage.setItem(
      `API_KEY_${settings.LLM_MODEL || models[0]}`,
      settings.LLM_API_KEY,
    );
  };

  let subtitle = t(I18nKey.CONFIGURATION$MODAL_SUB_TITLE);
  if (loading) {
    subtitle = t(I18nKey.CONFIGURATION$AGENT_LOADING);
  } else if (agentIsRunning) {
    subtitle = t(I18nKey.CONFIGURATION$AGENT_RUNNING);
  } else if (!settingsAreUpToDate()) {
    subtitle = t(I18nKey.CONFIGURATION$SETTINGS_NEED_UPDATE_MESSAGE);
  }
  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title={t(I18nKey.CONFIGURATION$MODAL_TITLE)}
      subtitle={subtitle}
      actions={[
        {
          label: t(I18nKey.CONFIGURATION$MODAL_SAVE_BUTTON_LABEL),
          action: handleSaveSettings,
          closeAfterAction: true,
          className: "bg-primary rounded-lg",
        },
        {
          label: t(I18nKey.CONFIGURATION$MODAL_CLOSE_BUTTON_LABEL),
          action: () => {
            setSettings(currentSettings); // reset settings from any changes
          },
          isDisabled: !settingsAreUpToDate(),
          closeAfterAction: true,
          className: "bg-neutral-500 rounded-lg",
        },
      ]}
    >
      {loading && <Spinner />}
      {!loading && (
        <SettingsForm
          disabled={agentIsRunning}
          settings={settings}
          models={models}
          agents={agents}
          onModelChange={handleModelChange}
          onAgentChange={handleAgentChange}
          onLanguageChange={handleLanguageChange}
          onAPIKeyChange={handleAPIKeyChange}
        />
      )}
    </BaseModal>
  );
}

export default SettingsModal;
