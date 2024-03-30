import React, { useEffect, useState } from "react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
  Button,
} from "@nextui-org/react";
import { Select, ConfigProvider, theme } from "antd";
import {
  AGENTS,
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
    cachedAgents.length > 0 ? cachedAgents : AGENTS,
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

  const filterOption = (
    input: string,
    option?: { label: string; value: string },
  ) => (option?.label ?? "").toLowerCase().includes(input.toLowerCase());

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      hideCloseButton
      isDismissable={false}
      backdrop="blur"
    >
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

            <ConfigProvider
              theme={{
                algorithm: theme.darkAlgorithm,
              }}
            >
              <Select
                showSearch
                size="large"
                placeholder="Select a model"
                onChange={setModel}
                defaultValue={model}
                filterOption={filterOption}
                options={supportedModels.map((v: string) => ({
                  value: v,
                  label: v,
                }))}
              />

              <Select
                showSearch
                size="large"
                placeholder="Select a agent"
                onChange={setAgent}
                defaultValue={agent}
                filterOption={filterOption}
                options={supportedAgents.map((v: string) => ({
                  value: v,
                  label: v,
                }))}
              />
            </ConfigProvider>
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
