import { useDisclosure } from "@nextui-org/react";
import React, { useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { OAuthPopup } from "@tasoskakour/react-use-oauth2";
import ChatInterface from "#/components/chat/ChatInterface";
import Errors from "#/components/Errors";
import { Container, Orientation } from "#/components/Resizable";
import Workspace from "#/components/Workspace";
import LoadPreviousSessionModal from "#/components/modals/load-previous-session/LoadPreviousSessionModal";
import SettingsModal from "#/components/modals/settings/SettingsModal";
import { fetchMsgTotal } from "#/services/session";
import Socket from "#/services/socket";
import { ResFetchMsgTotal } from "#/types/ResponseType";
import "./App.css";
import Terminal from "./components/terminal/Terminal";
import { initializeAgent } from "./services/agent";
import { settingsAreUpToDate } from "./services/settings";
import SigninModal from "#/components/modals/auth/SigninModal";
import { parseJwt } from "#/utils/auth";
import Controls from "#/components/Controls";

// React.StrictMode will cause double rendering, use this to prevent it
let initOnce = false;

function App(): JSX.Element {
  const [isWarned, setIsWarned] = useState(false);
  const [username, setUsername] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isGuest, setIsGuest] = useState(true);

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

  const {
    isOpen: authModalIsOpen,
    onOpen: onAuthModalOpen,
    onOpenChange: onAuthModalOpenChange,
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

  const loadUserInfo = () => {
    const data = parseJwt(localStorage.getItem("token") || "");
    if (data.username) {
      setUsername(data.username);
      setAvatarUrl(data.avatar_url);
    }
    if (data.provider) {
      setIsGuest(false);
    }
  };

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    loadUserInfo();

    if (!settingsAreUpToDate()) {
      onSettingsModalOpen();
    } else {
      initializeAgent();
    }

    Socket.registerCallback("open", [getMsgTotal]);

    getMsgTotal();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<Navigate to="/" />} />
        <Route path="/auth/callback" element={<OAuthPopup />} />
        <Route
          path="/"
          element={
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
              <Controls
                isGuest={isGuest}
                username={username}
                avatarUrl={avatarUrl}
                setAuthOpen={onAuthModalOpen}
                setSettingOpen={onSettingsModalOpen}
              />
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
              <SigninModal
                isOpen={authModalIsOpen}
                onOpenChange={() => {
                  loadUserInfo();
                  onAuthModalOpenChange();
                }}
              />
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
