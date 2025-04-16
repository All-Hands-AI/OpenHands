import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { useDisclosure, Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { BaseModal } from "#/components/shared/modals/base-modal/base-modal";
import React from "react";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const { t } = useTranslation();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();

  const ref = useTerminal({
    commands,
  });

  // Handle click on terminal to show modal
  const handleTerminalClick = (e: React.MouseEvent) => {
    onOpen();
  };

  const readOnlyMessage = "The terminal is read-only to avoid user interference with agent's task. If you would like to make some manual modifications to the system, please launch the VSCode server from Workspace.";

  return (
    <div className="h-full p-2 min-h-0 flex-grow">
      <Tooltip content={readOnlyMessage} placement="bottom">
        <div 
          ref={ref} 
          className="h-full w-full cursor-not-allowed" 
          onClick={handleTerminalClick}
        />
      </Tooltip>

      <BaseModal
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        title="Terminal is Read-Only"
        actions={[
          {
            label: "Close",
            onClick: () => onOpenChange(false),
            variant: "primary",
          },
        ]}
      >
        <p className="text-sm text-gray-300">
          {readOnlyMessage}
        </p>
      </BaseModal>
    </div>
  );
}

export default Terminal;
