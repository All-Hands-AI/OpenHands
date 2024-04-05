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
import i18next from "i18next";
import {
  INITIAL_AGENTS,
  fetchModels,
  fetchAgents,
  INITIAL_MODELS,
  sendSettings,
  getInitialModel,
} from "../services/settingsService";
import {
  setModel,
  setAgent,
  setWorkspaceDirectory,
  setLanguage,
} from "../state/settingsSlice";
import store, { RootState } from "../store";
import socket from "../socket/socket";
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
  const { t } = useTranslation();
  const model = useSelector((state: RootState) => state.settings.model);
  const agent = useSelector((state: RootState) => state.settings.agent);
  const workspaceDirectory = useSelector(
    (state: RootState) => state.settings.workspaceDirectory,
  );
  const language = useSelector((state: RootState) => state.settings.language);

  const [supportedModels, setSupportedModels] = useState(
    cachedModels.length > 0 ? cachedModels : INITIAL_MODELS,
  );
  const [supportedAgents, setSupportedAgents] = useState(
    cachedAgents.length > 0 ? cachedAgents : INITIAL_AGENTS,
  );

  useEffect(() => {
    async function setInitialModel() {
      const initialModel = await getInitialModel();
      store.dispatch(setModel(initialModel));
    }
    setInitialModel();

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
    const previousModel = localStorage.getItem("model");
    const previousWorkspaceDirectory =
      localStorage.getItem("workspaceDirectory");
    const previousAgent = localStorage.getItem("agent");

    if (
      model !== previousModel ||
      agent !== previousAgent ||
      workspaceDirectory !== previousWorkspaceDirectory
    ) {
      sendSettings(socket, { model, agent, workspaceDirectory, language });
    }

    localStorage.setItem("model", model);
    localStorage.setItem("workspaceDirectory", workspaceDirectory);
    localStorage.setItem("agent", agent);
    localStorage.setItem("language", language);
    i18next.changeLanguage(language);
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
              onChange={(e) =>
                store.dispatch(setWorkspaceDirectory(e.target.value))
              }
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
                store.dispatch(setModel(key as string));
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
                store.dispatch(setAgent(key as string));
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
              onChange={(e) => {
                store.dispatch(setLanguage(e.target.value));
              }}
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
