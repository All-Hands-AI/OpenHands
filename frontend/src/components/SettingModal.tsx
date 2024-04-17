import React, { useEffect, useState } from "react";
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
  saveSettings,
  getCurrentSettings,
} from "../services/settingsService";
import { I18nKey } from "../i18n/declaration";
import { AvailableLanguages } from "../i18n";
import { ArgConfigType } from "../types/ConfigType";
import ODModal from "./ODModal";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

function InnerSettingModal({ isOpen, onClose }: Props): JSX.Element {
  const settings = getCurrentSettings();
  const [model, setModel] = useState(settings.get(ArgConfigType.LLM_MODEL));
  const [inputModel, setInputModel] = useState(
    settings.get(ArgConfigType.LLM_MODEL),
  );
  const [agent, setAgent] = useState(settings.get(ArgConfigType.AGENT));
  const [language, setLanguage] = useState(
    settings.get(ArgConfigType.LANGUAGE),
  );

  const { t } = useTranslation();

  const [supportedModels, setSupportedModels] = useState([]);
  const [supportedAgents, setSupportedAgents] = useState([]);

  useEffect(() => {
    fetchModels().then((fetchedModels) => {
      const sortedModels = fetchedModels.sort(); // Sorting the models alphabetically
      setSupportedModels(sortedModels);
    });

    fetchAgents().then((fetchedAgents) => {
      setSupportedAgents(fetchedAgents);
    });
  }, []);

  const handleSaveCfg = () => {
    saveSettings({
      [ArgConfigType.LLM_MODEL]: model ?? inputModel,
      [ArgConfigType.AGENT]: agent,
      [ArgConfigType.LANGUAGE]: language,
    });
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
          selectedKeys={[language || ""]}
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
