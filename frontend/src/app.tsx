import { useDisclosure } from "@nextui-org/react";
import React, { useEffect } from "react";
import { Toaster } from "react-hot-toast";
import { IoLockClosed } from "react-icons/io5";
import ChatInterface from "#/components/chat/ChatInterface";
import Errors from "#/components/Errors";
import { Container, Orientation } from "#/components/Resizable";
import Workspace from "#/components/Workspace";
import LoadPreviousSessionModal from "#/components/modals/load-previous-session/LoadPreviousSessionModal";
import AgentControlBar from "./components/AgentControlBar";
import AgentStatusBar from "./components/AgentStatusBar";
import VolumeIcon from "./components/VolumeIcon";
import Terminal from "./components/terminal/Terminal";
import Session from "#/services/session";
import { getToken } from "#/services/auth";
import { getSettings } from "#/services/settings";
import Security from "./components/modals/security/Security";
import { ProjectMenuCard } from "./components/project-menu/ProjectMenuCard";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <AgentControlBar />
      </div>

      <AgentStatusBar />

      <div style={{ display: "flex", alignItems: "center" }}>
        <div style={{ marginRight: "8px" }}>
          <VolumeIcon />
        </div>
        {showSecurityLock && (
          <div
            className="cursor-pointer hover:opacity-80 transition-all"
            style={{ marginRight: "8px" }}
            onClick={() => setSecurityOpen(true)}
          >
            <IoLockClosed size={20} />
          </div>
        )}
      </div>

      <ProjectMenuCard />
    </div>
  );
}

// React.StrictMode will cause double rendering, use this to prevent it
let initOnce = false;

function App(): JSX.Element {
  const {
    isOpen: loadPreviousSessionModalIsOpen,
    onOpen: onLoadPreviousSessionModalOpen,
    onOpenChange: onLoadPreviousSessionModalOpenChange,
  } = useDisclosure();

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  const { SECURITY_ANALYZER } = getSettings();

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    if (getToken()) {
      onLoadPreviousSessionModalOpen();
    } else {
      Session.startNewSession();
    }
  }, []);

  return (
    <div className="h-full flex flex-col gap-[10px]">
      <div className="flex grow text-white min-h-0">
        <Container
          orientation={Orientation.HORIZONTAL}
          className="grow h-full min-h-0 min-w-0"
          initialSize={500}
          firstChild={<ChatInterface />}
          firstClassName="rounded-xl overflow-hidden border border-neutral-600"
          secondChild={
            <Container
              orientation={Orientation.VERTICAL}
              className="h-full min-h-0 min-w-0"
              initialSize={window.innerHeight - 300}
              firstChild={<Workspace />}
              firstClassName="rounded-xl border border-neutral-600 bg-neutral-800 flex flex-col overflow-hidden"
              secondChild={<Terminal />}
              secondClassName="rounded-xl border border-neutral-600 bg-neutral-800"
            />
          }
          secondClassName="flex flex-col overflow-hidden"
        />
      </div>
      <Controls
        setSecurityOpen={onSecurityModalOpen}
        showSecurityLock={!!SECURITY_ANALYZER}
      />
      <Security
        isOpen={securityModalIsOpen}
        onOpenChange={onSecurityModalOpenChange}
      />
      <LoadPreviousSessionModal
        isOpen={loadPreviousSessionModalIsOpen}
        onOpenChange={onLoadPreviousSessionModalOpenChange}
      />
      <Errors />
      <Toaster />
    </div>
  );
}

export default App;
