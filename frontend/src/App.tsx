import React, { useState } from "react";
import "./App.css";
import { useSelector } from "react-redux";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import SettingModal from "./components/SettingModal";
import Workspace from "./components/Workspace";
import assistantAvatar from "./assets/assistant-avatar.png";
import { RootState } from "./store";

function InitializingStatus(): JSX.Element {
  return (
    <div className="flex items-center m-auto h-full">
      <img
        src={assistantAvatar}
        alt="assistant avatar"
        className="w-[40px] h-[40px] mx-2.5"
      />
      <div>Initializing agent (may take up to 10 seconds)...</div>
    </div>
  );
}

function App(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.task);
  const [settingOpen, setSettingOpen] = useState(false);

  const handleCloseModal = () => {
    setSettingOpen(false);
  };

  return (
    <div className="flex h-screen bg-bg-dark text-white">
      <Errors />
      {!initialized ? (
        <InitializingStatus />
      ) : (
        <>
          <div className="flex-1 rounded-xl m-4 overflow-hidden bg-bg-light">
            <ChatInterface setSettingOpen={setSettingOpen} />
          </div>
          <div className="flex flex-col flex-1 m-4 overflow-hidden rounded-xl bg-bg-light">
            <Workspace />
          </div>

          <SettingModal isOpen={settingOpen} onClose={handleCloseModal} />
        </>
      )}
    </div>
  );
}

export default App;
