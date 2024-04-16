import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import {
  Autocomplete,
  AutocompleteItem,
  Button,
  Select,
  SelectItem,
} from "@nextui-org/react";
import { KeyboardEvent } from "@react-types/shared/src/events";
import { useTranslation } from "react-i18next";
import {
  fetchAgents,
  fetchModels,
  INITIAL_AGENTS,
  INITIAL_MODELS,
  saveSettings,
} from "../services/settingsService";
import { RootState } from "../store";
import { I18nKey } from "../i18n/declaration";
import { AvailableLanguages } from "../i18n";
import { ArgConfigType } from "../types/ConfigType";
import ODModal from "./ODModal";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const cachedModels = JSON.parse(
  localStorage.getItem("supportedModels") || "[]",
);
const cachedAgents = JSON.parse(
  localStorage.getItem("supportedAgents") || "[]",
);

function InnerSettingModal({ isOpen, onClose }: Props): JSX.Element {
  const settings = useSelector((state: RootState) => state.settings);
  const [model, setModel] = useState(settings[ArgConfigType.LLM_MODEL]);
  const [inputModel, setInputModel] = useState(
    settings[ArgConfigType.LLM_MODEL],
  );
  const [agent, setAgent] = useState(settings[ArgConfigType.AGENT]);
  const [language, setLanguage] = useState(settings[ArgConfigType.LANGUAGE]);

  const { t } = useTranslation();

  const [supportedModels, setSupportedModels] = useState(
    cachedModels.length > 0 ? cachedModels : INITIAL_MODELS,
  );
  const [supportedAgents, setSupportedAgents] = useState(
    cachedAgents.length > 0 ? cachedAgents : INITIAL_AGENTS,
  );

  useEffect(() => {
    fetchModels().then((fetchedModels) => {
      const sortedModels = fetchedModels.sort(); // Sorting the models alphabetically
      setSupportedModels(sortedModels);
      localStorage.setItem("supportedModels", JSON.stringify(sortedModels));
    });

    fetchAgents().then((fetchedAgents) => {
      setSupportedAgents(fetchedAgents);
      localStorage.setItem("supportedAgents", JSON.stringify(fetchedAgents));
    });
  }, []);

  const handleSaveCfg = () => {
    saveSettings(
      {
        [ArgConfigType.LLM_MODEL]: model ?? inputModel,
        [ArgConfigType.AGENT]: agent,
        [ArgConfigType.LANGUAGE]: language,
      },
      Object.fromEntries(
        Object.entries(settings).map(([key, value]) => [key, value]),
      ),
      false,
    );
    onClose();
  };

  const customFilter = (item: string, input: string) =>
    item.toLowerCase().includes(input.toLowerCase());

  return (
    <ODModal
      isOpen={isOpen}
      onClose={onClose}
      title={t(I18nKey.CONFIGURATION$MODAL_TITLE)}
      subtitle={t(I18nKey.CONFIGURATION$MODAL_SUB_TITLE)}
      hideCloseButton
      backdrop="blur"
      size="sm"
      primaryAction={
        <Button className="bg-primary rounded-small" onPress={handleSaveCfg}>
          {t(I18nKey.CONFIGURATION$MODAL_SAVE_BUTTON_LABEL)}
        </Button>
      }
      secondaryAction={
        <Button className="bg-neutral-500 rounded-small" onPress={onClose}>
          {t(I18nKey.CONFIGURATION$MODAL_CLOSE_BUTTON_LABEL)}
        </Button>
      }
    >
      <>
        <Autocomplete
          defaultItems={supportedModels.map((v: string) => ({
            label: v,
            value: v,
          }))}
          label={t(I18nKey.CONFIGURATION$MODEL_SELECT_LABEL)}
          placeholder={t(I18nKey.CONFIGURATION$MODEL_SELECT_PLACEHOLDER)}
          selectedKey={model}
          onSelectionChange={(key) => {
            setModel(key as string);
          }}
          onInputChange={(e) => setInputModel(e)}
          onKeyDown={(e: KeyboardEvent) => e.continuePropagation()}
          defaultFilter={customFilter}
          defaultInputValue={inputModel}
          allowsCustomValue
        >
          {(item: { label: string; value: string }) => (
            <AutocompleteItem key={item.value} value={item.value}>
              {item.label}
            </AutocompleteItem>
          )}
        </Autocomplete>
        <Autocomplete
          defaultItems={supportedAgents.map((v: string) => ({
            label: v,
            value: v,
          }))}
          label={t(I18nKey.CONFIGURATION$AGENT_SELECT_LABEL)}
          placeholder={t(I18nKey.CONFIGURATION$AGENT_SELECT_PLACEHOLDER)}
          defaultSelectedKey={agent}
          onSelectionChange={(key) => {
            setAgent(key as string);
          }}
          onKeyDown={(e: KeyboardEvent) => e.continuePropagation()}
          defaultFilter={customFilter}
        >
          {(item: { label: string; value: string }) => (
            <AutocompleteItem key={item.value} value={item.value}>
              {item.label}
            </AutocompleteItem>
          )}
        </Autocomplete>
        <Select
          selectionMode="single"
          onChange={(e) => setLanguage(e.target.value)}
          selectedKeys={[language]}
          label={t(I18nKey.CONFIGURATION$LANGUAGE_SELECT_LABEL)}
        >
          {AvailableLanguages.map((lang) => (
            <SelectItem key={lang.value} value={lang.value}>
              {lang.label}
            </SelectItem>
          ))}
        </Select>
      </>
    </ODModal>
  );
}

function SettingModal({ isOpen, onClose }: Props): JSX.Element {
  // Do not render the modal if it is not open, prevents reading empty from localStorage after initialization
  if (!isOpen) return <div />;
  return <InnerSettingModal isOpen={isOpen} onClose={onClose} />;
}

export default SettingModal;
