import React, { useEffect, useState } from "react";
import "./App.css";
import { Toaster } from "react-hot-toast";
import CogTooth from "./assets/cog-tooth";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import LoadMessageModal from "./components/LoadMessageModal";
import { Container, Orientation } from "./components/Resizable";
import SettingModal from "./components/SettingModal";
import Terminal from "./components/Terminal";
import Workspace from "./components/Workspace";
import { fetchMsgTotal } from "./services/session";
import { initializeAgent } from "./services/settingsService";
import Socket from "./services/socket";
import { ResFetchMsgTotal } from "./types/ResponseType";
import SettingsForm from "./components/settings/SettingsForm";

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
  const [isWarned, setIsWarned] = useState(false);
  const [loadMsgWarning, setLoadMsgWarning] = useState(false);

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

  const handleCloseModal = () => {
    setSettingOpen(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col">
      <SettingsForm />
    </div>
  );
}

export default App;
