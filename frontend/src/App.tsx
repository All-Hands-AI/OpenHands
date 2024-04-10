import React, { useEffect, useState } from "react";
import "./App.css";
import { Toaster } from "react-hot-toast";
import CogTooth from "./assets/cog-tooth";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import SettingModal from "./components/SettingModal";
import Terminal from "./components/Terminal";
import Workspace from "./components/Workspace";
import { fetchMsgTotal } from "./services/session";
import LoadMessageModal from "./components/LoadMessageModal";
import { ResConfigurations, ResFetchMsgTotal } from "./types/ResponseType";
import { fetchConfigurations, saveSettings } from "./services/settingsService";
import Socket from "./services/socket";
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
    <div className="flex h-screen bg-neutral-900 text-white">
      <LeftNav setSettingOpen={setSettingOpen} />
      <div className="flex flex-col grow gap-3 py-3 pr-3">
        <div className="flex gap-3 grow min-h-0">
          <div className="w-[500px] shrink-0 rounded-xl overflow-hidden border border-neutral-600">
            <ChatInterface />
          </div>
          <div className="flex flex-col flex-1 overflow-hidden rounded-xl bg-neutral-800 border border-neutral-600">
            <Workspace />
          </div>
        </div>
        <div className="h-72 shrink-0 bg-neutral-800 rounded-xl border border-neutral-600 flex flex-col">
          <Terminal key="terminal" />
        </div>
      </div>
      <SettingModal isOpen={settingOpen} onClose={handleCloseModal} />

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
