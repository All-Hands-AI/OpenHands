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
} from "@nextui-org/react";
import { KeyboardEvent } from "@react-types/shared/src/events";
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
} from "../state/settingsSlice";
import store, { RootState } from "../store";
import socket from "../socket/socket";

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
  const model = useSelector((state: RootState) => state.settings.model);
  const agent = useSelector((state: RootState) => state.settings.agent);
  const workspaceDirectory = useSelector(
    (state: RootState) => state.settings.workspaceDirectory,
  );

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
    sendSettings(socket, { model, agent, workspaceDirectory });
    localStorage.setItem("model", model);
    localStorage.setItem("workspaceDirectory", workspaceDirectory);
    localStorage.setItem("agent", agent);
    onClose();
  };

  const customFilter = (item: string, input: string) =>
    item.toLowerCase().includes(input.toLowerCase());

  return (
    <Modal isOpen={isOpen} onClose={onClose} hideCloseButton backdrop="blur">
      <ModalContent>
        <>
          <ModalHeader className="flex flex-col gap-1">
            Configuration
          </ModalHeader>
          <ModalBody>
            <Input
              type="text"
              label="OpenDevin Workspace Directory"
              defaultValue={workspaceDirectory}
              placeholder="Default: ./workspace"
              onChange={(e) =>
                store.dispatch(setWorkspaceDirectory(e.target.value))
              }
            />

            <Autocomplete
              defaultItems={supportedModels.map((v: string) => ({
                label: v,
                value: v,
              }))}
              label="Model"
              placeholder="Select a model"
              selectedKey={model}
              // className="max-w-xs"
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
              label="Agent"
              placeholder="Select a agent"
              defaultSelectedKey={agent}
              // className="max-w-xs"
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
          </ModalBody>

          <ModalFooter>
            <Button color="danger" variant="light" onPress={onClose}>
              Close
            </Button>
            <Button color="primary" onPress={handleSaveCfg}>
              Save
            </Button>
          </ModalFooter>
        </>
      </ModalContent>
    </Modal>
  );
}

export default SettingModal;
