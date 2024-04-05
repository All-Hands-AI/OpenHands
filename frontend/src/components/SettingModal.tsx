import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
  Button,
  Autocomplete,
  AutocompleteItem,
  Select,
  SelectItem,
} from "@nextui-org/react";
import { KeyboardEvent } from "@react-types/shared/src/events";
import { useTranslation } from "react-i18next";
import {
  INITIAL_AGENTS,
  fetchModels,
  fetchAgents,
  INITIAL_MODELS,
  saveSettings,
  getInitialModel,
} from "../services/settingsService";
import { RootState } from "../store";
import { I18nKey } from "../i18n/declaration";
import { AvailableLanguages } from "../i18n";

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

function SettingModal({ isOpen, onClose }: Props): JSX.Element {
  const defModel = useSelector((state: RootState) => state.settings.model);
  const [model, setModel] = useState(defModel);
  const defAgent = useSelector((state: RootState) => state.settings.agent);
  const [agent, setAgent] = useState(defAgent);
  const defWorkspaceDirectory = useSelector(
    (state: RootState) => state.settings.workspaceDirectory,
  );
  const [workspaceDirectory, setWorkspaceDirectory] = useState(
    defWorkspaceDirectory,
  );
  const defLanguage = useSelector(
    (state: RootState) => state.settings.language,
  );
  const [language, setLanguage] = useState(defLanguage);

  const { t } = useTranslation();

  const [supportedModels, setSupportedModels] = useState(
    cachedModels.length > 0 ? cachedModels : INITIAL_MODELS,
  );
  const [supportedAgents, setSupportedAgents] = useState(
    cachedAgents.length > 0 ? cachedAgents : INITIAL_AGENTS,
  );

  useEffect(() => {
    getInitialModel()
      .then((initialModel) => {
        setModel(initialModel);
      })
      .catch();

    fetchModels().then((fetchedModels) => {
      setSupportedModels(fetchedModels);
      localStorage.setItem("supportedModels", JSON.stringify(fetchedModels));
    });
    fetchAgents().then((fetchedAgents) => {
      setSupportedAgents(fetchedAgents);
      localStorage.setItem("supportedAgents", JSON.stringify(fetchedAgents));
    });
  }, []);

  const handleSaveCfg = () => {
    saveSettings(
      { model, agent, workspaceDirectory, language },
      model !== defModel &&
        agent !== defAgent &&
        workspaceDirectory !== defWorkspaceDirectory,
    );
    onClose();
  };

  const customFilter = (item: string, input: string) =>
    item.toLowerCase().includes(input.toLowerCase());

  return (
    <Modal isOpen={isOpen} onClose={onClose} hideCloseButton backdrop="blur">
      <ModalContent>
        <>
          <ModalHeader className="flex flex-col gap-1">
            {t(I18nKey.CONFIGURATION$MODAL_TITLE)}
          </ModalHeader>
          <ModalBody>
            <Input
              type="text"
              label={t(
                I18nKey.CONFIGURATION$OPENDEVIN_WORKSPACE_DIRECTORY_INPUT_LABEL,
              )}
              defaultValue={workspaceDirectory}
              placeholder={t(
                I18nKey.CONFIGURATION$OPENDEVIN_WORKSPACE_DIRECTORY_INPUT_PLACEHOLDER,
              )}
              onChange={(e) => setWorkspaceDirectory(e.target.value)}
            />

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
              onKeyDown={(e: KeyboardEvent) => e.continuePropagation()}
              defaultFilter={customFilter}
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
          </ModalBody>

          <ModalFooter>
            <Button color="danger" variant="light" onPress={onClose}>
              {t(I18nKey.CONFIGURATION$MODAL_CLOSE_BUTTON_LABEL)}
            </Button>
            <Button color="primary" onPress={handleSaveCfg}>
              {t(I18nKey.CONFIGURATION$MODAL_SAVE_BUTTON_LABEL)}
            </Button>
          </ModalFooter>
        </>
      </ModalContent>
    </Modal>
  );
}

export default SettingModal;
