import { useDisclosure } from "@nextui-org/react";
import React, { useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
import CogTooth from "#/assets/cog-tooth";
import ChatInterface from "#/components/ChatInterface";
import Errors from "#/components/Errors";
import { Container, Orientation } from "#/components/Resizable";
import Workspace from "#/components/Workspace";
import LoadPreviousSessionModal from "#/components/modals/load-previous-session/LoadPreviousSessionModal";
import SettingsModal from "#/components/modals/settings/SettingsModal";
import { fetchMsgTotal } from "#/services/session";
import Socket from "#/services/socket";
import { ResFetchMsgTotal } from "#/types/ResponseType";
import "./App.css";
import AgentControlBar from "./components/AgentControlBar";
import AgentStatusBar from "./components/AgentStatusBar";
import Terminal from "./components/terminal/Terminal";
import { reconnectAgent } from "./services/agent";
import { getSettings } from "./services/settings";

interface Props {
  setSettingOpen: (isOpen: boolean) => void;
}

function Controls({ setSettingOpen }: Props): JSX.Element {
  return (
    <div className="flex w-full p-4 bg-neutral-900 items-center shrink-0 justify-between">
      <div className="flex items-center gap-4">
        <AgentControlBar />
      </div>
      <AgentStatusBar />
      <div
        className="cursor-pointer hover:opacity-80 transition-all"
        onClick={() => setSettingOpen(true)}
      >
        <CogTooth />
      </div>
    </div>
  );
}

// React.StrictMode will cause double rendering, use this to prevent it
let initOnce = false;

function App(): JSX.Element {
  const [isWarned, setIsWarned] = useState(false);

  const {
    isOpen: settingsModalIsOpen,
    onOpen: onSettingsModalOpen,
    onOpenChange: onSettingsModalOpenChange,
  } = useDisclosure();

  const {
    isOpen: loadPreviousSessionModalIsOpen,
    onOpen: onLoadPreviousSessionModalOpen,
    onOpenChange: onLoadPreviousSessionModalOpenChange,
  } = useDisclosure();

  const getMsgTotal = () => {
    if (isWarned) return;
    fetchMsgTotal()
      .then((data: ResFetchMsgTotal) => {
        if (data.msg_total > 0) {
          onLoadPreviousSessionModalOpen();
          setIsWarned(true);
        }
      })
      .catch();
  };

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    reconnectAgent(getSettings());

    Socket.registerCallback("open", [getMsgTotal]);

    getMsgTotal();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col">
      <div className="flex grow bg-neutral-900 text-white min-h-0">
        <Container
          orientation={Orientation.HORIZONTAL}
          className="grow h-full min-h-0 min-w-0 px-3 pt-3"
          initialSize={500}
          firstChild={<ChatInterface />}
          firstClassName="min-w-[500px] rounded-xl overflow-hidden border border-neutral-600"
          secondChild={
            <Container
              orientation={Orientation.VERTICAL}
              className="grow h-full min-h-0 min-w-0"
              initialSize={window.innerHeight - 300}
              firstChild={<Workspace />}
              firstClassName="min-h-72 rounded-xl border border-neutral-600 bg-neutral-800 flex flex-col overflow-hidden"
              secondChild={<Terminal />}
              secondClassName="min-h-72 rounded-xl border border-neutral-600 bg-neutral-800"
            />
          }
          secondClassName="flex flex-col overflow-hidden grow min-w-[500px]"
        />
      </div>
      <Controls setSettingOpen={onSettingsModalOpen} />
      <SettingsModal
        isOpen={settingsModalIsOpen}
        onOpenChange={onSettingsModalOpenChange}
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
