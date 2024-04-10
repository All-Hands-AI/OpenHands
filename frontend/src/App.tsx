import React, { useEffect, useState } from "react";
import "./App.css";
import CogTooth from "./assets/cog-tooth";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import LoadMessageModal from "./components/LoadMessageModal";
import { Container, Orientation } from "./components/Resizable";
import SettingModal from "./components/SettingModal";
import Terminal from "./components/Terminal";
import Workspace from "./components/Workspace";
import { fetchMsgTotal } from "./services/session";
import { fetchConfigurations, saveSettings } from "./services/settingsService";
import Socket from "./services/socket";
import { ResConfigurations, ResFetchMsgTotal } from "./types/ResponseType";
import { getCachedConfig } from "./utils/storage";

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
  const [settingOpen, setSettingOpen] = useState(false);
  const [loadMsgWarning, setLoadMsgWarning] = useState(false);

  const getConfigurations = () => {
    fetchConfigurations()
      .then((data: ResConfigurations) => {
        const settings = getCachedConfig();

        saveSettings(
          Object.fromEntries(
            Object.entries(data).map(([key, value]) => [key, String(value)]),
          ),
          settings,
          true,
        );
      })
      .catch();
  };

  const getMsgTotal = () => {
    fetchMsgTotal()
      .then((data: ResFetchMsgTotal) => {
        if (data.msg_total > 0) {
          setLoadMsgWarning(true);
        }
      })
      .catch();
  };

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    Socket.registerCallback("open", [getConfigurations, getMsgTotal]);

    getConfigurations();
    getMsgTotal();
  }, []);

  const handleCloseModal = () => {
    setSettingOpen(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col">
      <div className="flex grow bg-neutral-900 text-white min-h-0">
        <LeftNav setSettingOpen={setSettingOpen} />
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
      <SettingModal isOpen={settingOpen} onClose={handleCloseModal} />
      <LoadMessageModal
        isOpen={loadMsgWarning}
        onClose={() => setLoadMsgWarning(false)}
      />
      <Errors />
    </div>
  );
}

export default App;
