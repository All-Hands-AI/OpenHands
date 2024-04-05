import React, { useState } from "react";
import "./App.css";
import CogTooth from "./assets/cog-tooth";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import SettingModal from "./components/SettingModal";
import Terminal from "./components/Terminal";
import Workspace from "./components/Workspace";

interface Props {
  setSettingOpen: (isOpen: boolean) => void;
}

function LeftNav({ setSettingOpen }: Props): JSX.Element {
  return (
    <div className="flex flex-col h-full p-4 bg-bg-dark w-16 items-center shrink-0">
      <div
        className="mt-auto cursor-pointer hover:opacity-80"
        onClick={() => setSettingOpen(true)}
      >
        <CogTooth />
      </div>
    </div>
  );
}

function App(): JSX.Element {
  const [settingOpen, setSettingOpen] = useState(false);

  const handleCloseModal = () => {
    setSettingOpen(false);
  };

  return (
    <div className="flex h-screen bg-bg-dark text-white">
      <LeftNav setSettingOpen={setSettingOpen} />
      <div className="flex flex-col grow gap-3 py-3 pr-3">
        <div className="flex gap-3 grow min-h-0">
          <div className="w-[500px] shrink-0 rounded-xl overflow-hidden border border-border">
            <ChatInterface />
          </div>
          <div className="flex flex-col flex-1 overflow-hidden rounded-xl bg-bg-workspace border border-border">
            <Workspace />
          </div>
        </div>
        <div className="h-72 shrink-0 bg-bg-workspace rounded-xl border border-border flex flex-col">
          <Terminal key="terminal" />
        </div>
      </div>
      <SettingModal isOpen={settingOpen} onClose={handleCloseModal} />
      <Errors />
    </div>
  );
}

export default App;
