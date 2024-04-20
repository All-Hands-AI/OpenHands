import React, { useEffect, useState } from "react";
import "./App.css";
import { Toaster } from "react-hot-toast";
import { useDisclosure } from "@nextui-org/react";
import CogTooth from "./assets/cog-tooth";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import LoadMessageModal from "./components/LoadMessageModal";
import { Container, Orientation } from "./components/Resizable";
import Terminal from "./components/Terminal";
import Workspace from "./components/Workspace";
import { fetchMsgTotal } from "./services/session";
import { initializeAgent } from "./services/settingsService";
import Socket from "./services/socket";
import { ResFetchMsgTotal } from "./types/ResponseType";
import Settings from "./components/settings/SettingsModal";

interface Props {
  setSettingOpen: (isOpen: boolean) => void;
}

function LeftNav({ setSettingOpen }: Props): JSX.Element {
  return (
    <div className="flex flex-col h-full p-4 bg-neutral-900 w-16 items-center shrink-0">
      <div
        className="mt-auto cursor-pointer hover:opacity-80"
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
  const [loadMsgWarning, setLoadMsgWarning] = useState(false);

  const { isOpen, onOpen, onOpenChange } = useDisclosure();

  const getMsgTotal = () => {
    if (isWarned) return;
    fetchMsgTotal()
      .then((data: ResFetchMsgTotal) => {
        if (data.msg_total > 0) {
          setLoadMsgWarning(true);
          setIsWarned(true);
        }
      })
      .catch();
  };

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    initializeAgent();

    Socket.registerCallback("open", [getMsgTotal]);

    getMsgTotal();
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col">
      <div className="flex grow bg-neutral-900 text-white min-h-0">
        <LeftNav setSettingOpen={onOpen} />
        <Container
          orientation={Orientation.VERTICAL}
          className="grow p-3 py-3 pr-3 min-w-0"
          initialSize={window.innerHeight - 300}
          firstChild={
            <Container
              orientation={Orientation.HORIZONTAL}
              className="grow h-full min-h-0 min-w-0"
              initialSize={500}
              firstChild={<ChatInterface />}
              firstClassName="min-w-[500px] rounded-xl overflow-hidden border border-neutral-600"
              secondChild={<Workspace />}
              secondClassName="flex flex-col overflow-hidden rounded-xl bg-neutral-800 border border-neutral-600 grow min-w-[500px] min-w-[500px]"
            />
          }
          firstClassName="min-h-72"
          secondChild={<Terminal key="terminal" />}
          secondClassName="min-h-72 bg-neutral-800 rounded-xl border border-neutral-600 flex flex-col"
        />
      </div>
      {/* This div is for the footer that will be added later
      <div className="h-8 w-full border-t border-border px-2" />
      */}
      <Settings isOpen={isOpen} onOpenChange={onOpenChange} />
      <LoadMessageModal
        isOpen={loadMsgWarning}
        onClose={() => setLoadMsgWarning(false)}
      />
      <Errors />
      <Toaster />
    </div>
  );
}

export default App;
