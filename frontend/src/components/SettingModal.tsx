import React from "react";
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

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  workspaceDir: string;
  setWorkspaceDir: (v: string) => void;
  model: string;
  setModel: (v: string) => void;
  supportedModels: string[];
  agent: string;
  setAgent: (v: string) => void;
  supportedAgents: string[];
}

function SettingModal({
  isOpen,
  onClose,
  onSave,
  workspaceDir,
  setWorkspaceDir,
  model,
  setModel,
  supportedModels,
  agent,
  setAgent,
  supportedAgents,
}: Props): JSX.Element {
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
              defaultValue={workspaceDir}
              placeholder="Default: ./workspace"
              onChange={(e) => setWorkspaceDir(e.target.value)}
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
                options={supportedModels.map((v) => ({
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
                options={supportedAgents.map((v) => ({
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
            <Button color="primary" onPress={onSave}>
              Save
            </Button>
          </ModalFooter>
        </>
      </ModalContent>
    </Modal>
  );
}

export default SettingModal;
