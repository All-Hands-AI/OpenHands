import React, { useEffect, useState } from "react";
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
  changeAgent,
  changeDirectory as sendChangeDirectorySocketMessage,
  changeModel,
  fetchModels,
  INITIAL_MODELS,
} from "../services/settingsService";

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
  const [workspaceDirectory, setWorkspaceDirectory] = useState(
    localStorage.getItem("workspaceDirectory") || "./workspace",
  );
  const [model, setModel] = useState(
    localStorage.getItem("model") || "gpt-3.5-turbo-1106",
  );
  const [supportedModels, setSupportedModels] = useState(
    cachedModels.length > 0 ? cachedModels : INITIAL_MODELS,
  );
  const [agent, setAgent] = useState(
    localStorage.getItem("agent") || "LangchainsAgent",
  );
  const [supportedAgents] = useState(
    cachedAgents.length > 0 ? cachedAgents : INITIAL_AGENTS,
  );

  useEffect(() => {
    fetchModels().then((fetchedModels) => {
      setSupportedModels(fetchedModels);
      localStorage.setItem("supportedModels", JSON.stringify(fetchedModels));
    });
  }, []);

  const handleSaveCfg = () => {
    sendChangeDirectorySocketMessage(workspaceDirectory);
    changeModel(model);
    changeAgent(agent);
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
              onChange={(e) => setWorkspaceDirectory(e.target.value)}
            />

            <Autocomplete
              defaultItems={supportedModels.map((v: string) => ({
                label: v,
                value: v,
              }))}
              label="Model"
              placeholder="Select a model"
              defaultSelectedKey={model}
              // className="max-w-xs"
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
              label="Agent"
              placeholder="Select a agent"
              defaultSelectedKey={agent}
              // className="max-w-xs"
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
