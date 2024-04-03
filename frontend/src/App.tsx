import React, { useEffect, useState } from "react";
import "./App.css";
import { useSelector } from "react-redux";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import SettingModal from "./components/SettingModal";
import Workspace from "./components/Workspace";
import store, { RootState } from "./store";
import { setInitialized } from "./state/globalSlice";
import { fetchMsgTotal } from "./socket/session";
import LoadMessageModal from "./components/LoadMessageModal";
import { ResFetchMsgTotal } from "./types/ResponseType";

function App(): JSX.Element {
  const { initialized } = useSelector((state: RootState) => state.global);
  const [settingOpen, setSettingOpen] = useState(false);
  const [loadMsgWarning, setLoadMsgWarning] = useState(false);

  useEffect(() => {
    if (!initialized) {
      fetchMsgTotal()
        .then((data: ResFetchMsgTotal) => {
          if (data.msg_total > 0) {
            setLoadMsgWarning(true);
          }
          store.dispatch(setInitialized(true));
        })
        .catch();
    }
  }, []);

  const handleCloseModal = () => {
    setSettingOpen(false);
  };

  return (
    <div className="flex h-screen bg-bg-dark text-white">
      <Errors />
      <div className="flex-1 rounded-xl m-4 overflow-hidden bg-bg-light">
        <ChatInterface setSettingOpen={setSettingOpen} />
      </div>
      <div className="flex flex-col flex-1 m-4 overflow-hidden rounded-xl bg-bg-light">
        <Workspace />
      </div>

      <SettingModal isOpen={settingOpen} onClose={handleCloseModal} />

      <LoadMessageModal
        isOpen={loadMsgWarning}
        onClose={() => setLoadMsgWarning(false)}
      />
    </div>
  );
}

export default App;
