import { Spinner } from "@nextui-org/react";
import i18next from "i18next";
import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { fetchAgents, fetchModels } from "#/services/options";
import { I18nKey } from "#/i18n/declaration";
import Session from "#/services/session";
import store, { RootState } from "../../../store";
import AgentState from "../../../types/AgentState";
import {
  Settings,
  getSettings,
  getDefaultSettings,
  getSettingsDifference,
  getValueConverter,
  settingsAreUpToDate,
  maybeMigrateSettings,
  saveSettings,
} from "#/services/settings";
import toast from "#/utils/toast";
import BaseModal from "../base-modal/BaseModal";
import SettingsForm from "./SettingsForm";
import { codeSlice } from "#/state/codeSlice";
import { listFiles } from "#/services/fileService";

interface SettingsProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const REQUIRED_SETTINGS = ["LLM_MODEL", "AGENT"];

function SettingsModal({ isOpen, onOpenChange }: SettingsProps) {
  const { t } = useTranslation();

  const [models, setModels] = React.useState<string[]>([]);
  const [agents, setAgents] = React.useState<string[]>([]);
  const [settings, setSettings] = React.useState<Settings>({} as Settings);
  const [workspaceSubdirs, setWorkspaceSubdirs] = React.useState<string[]>([]);
  const [agentIsRunning, setAgentIsRunning] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState(true);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  useEffect(() => {
    maybeMigrateSettings();
    setSettings(getSettings());
  }, []);

  useEffect(() => {
    const isRunning =
      curAgentState === AgentState.RUNNING ||
      curAgentState === AgentState.PAUSED ||
      curAgentState === AgentState.AWAITING_USER_INPUT;
    setAgentIsRunning(isRunning);
  }, [curAgentState]);

  React.useEffect(() => {
    (async () => {
      try {
        setModels(await fetchModels());
        setAgents(await fetchAgents());
        setWorkspaceSubdirs(
          (await listFiles("/", true)).map((d) => d.substring(1, d.length - 1)),
        );
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

  const handleWorkspaceChange = (workspaceSubdir: string) => {
    setSettings((prev) => ({ ...prev, WORKSPACE_SUBDIR: workspaceSubdir }));
  };

  const handleLanguageChange = (language: string) => {
    setSettings((prev) => ({ ...prev, LANGUAGE: language }));
  };

  const handleAPIKeyChange = (key: string) => {
    setSettings((prev) => ({ ...prev, LLM_API_KEY: key }));
  };

  const handleResetSettings = () => {
    setSettings(getDefaultSettings);
  };

  const handleSaveSettings = () => {
    const updatedSettings = getSettingsDifference(getSettings(), settings);
    saveSettings(settings);
    i18next.changeLanguage(settings.LANGUAGE);
    Session.startNewSession();

    const sensitiveKeys = ["LLM_API_KEY"];

    Object.entries(updatedSettings).forEach(([key, value]) => {
      if (!sensitiveKeys.includes(key)) {
        toast.settingsChanged(
          `${key} set to ${getValueConverter(key as keyof Settings)(value)}`,
        );
      } else {
        toast.settingsChanged(`${key} has been updated securely.`);
      }
    });
    if (Object.hasOwn(updatedSettings, "WORKSPACE_SUBDIR")) {
      store.dispatch(
        codeSlice.actions.updateWorkspace(updatedSettings.WORKSPACE_SUBDIR),
      );
    }
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
  const saveIsDisabled = REQUIRED_SETTINGS.some(
    (key) => !settings[key as keyof Settings],
  );

  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title={t(I18nKey.CONFIGURATION$MODAL_TITLE)}
      isDismissable={settingsAreUpToDate()}
      subtitle={subtitle}
      actions={[
        {
          label: t(I18nKey.CONFIGURATION$MODAL_SAVE_BUTTON_LABEL),
          action: handleSaveSettings,
          isDisabled: saveIsDisabled,
          closeAfterAction: true,
          className: "bg-primary rounded-lg",
        },
        {
          label: t(I18nKey.CONFIGURATION$MODAL_RESET_BUTTON_LABEL),
          action: handleResetSettings,
          closeAfterAction: false,
          className: "bg-neutral-500 rounded-lg",
        },
        {
          label: t(I18nKey.CONFIGURATION$MODAL_CLOSE_BUTTON_LABEL),
          action: () => {
            setSettings(getSettings()); // reset settings from any changes
          },
          isDisabled: !settingsAreUpToDate(),
          closeAfterAction: true,
          className: "bg-rose-600 rounded-lg",
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
          workspaceSubdirs={workspaceSubdirs}
          onModelChange={handleModelChange}
          onAgentChange={handleAgentChange}
          onLanguageChange={handleLanguageChange}
          onAPIKeyChange={handleAPIKeyChange}
          onWorkspaceChange={handleWorkspaceChange}
        />
      )}
    </BaseModal>
  );
}

export default SettingsModal;
