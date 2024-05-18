import {
  Dropdown,
  DropdownItem,
  DropdownMenu,
  DropdownSection,
  DropdownTrigger,
  useDisclosure,
  User,
} from "@nextui-org/react";
import React, { useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { OAuthPopup } from "@tasoskakour/react-use-oauth2";
import { IoMdLogIn, IoMdLogOut } from "react-icons/io";
import { AiOutlineSetting } from "react-icons/ai";
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
import AgentControlBar from "./components/AgentControlBar";
import AgentStatusBar from "./components/AgentStatusBar";
import Terminal from "./components/terminal/Terminal";
import { initializeAgent } from "./services/agent";
import { settingsAreUpToDate } from "./services/settings";
import SigninModal from "#/components/modals/auth/SigninModal";
import { parseJwt } from "#/utils/auth";

interface Props {
  isGuest: boolean;
  username: string;
  avatarUrl: string;
  setAuthOpen: (isOpen: boolean) => void;
  setSettingOpen: (isOpen: boolean) => void;
}

function Controls({
  isGuest,
  username,
  avatarUrl,
  setAuthOpen,
  setSettingOpen,
}: Props): JSX.Element {
  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.reload();
  };

  return (
    <div className="flex w-full p-4 bg-neutral-900 items-center shrink-0 justify-between">
      <div className="flex items-center gap-4">
        <AgentControlBar />
      </div>
      <AgentStatusBar />
      <Dropdown>
        <DropdownTrigger>
          <User
            name={
              <div className="font-bold text-base max-w-[30px] sm:max-w-[70px] md:max-w-[110px] lg:max-w-[180px] truncate">
                {username || "Guest"}
              </div>
            }
            avatarProps={{
              src: avatarUrl,
            }}
            className="cursor-pointer hover:opacity-80 transition-all mr-4"
          />
        </DropdownTrigger>
        <DropdownMenu aria-label="Static Actions">
          <DropdownSection showDivider>
            <DropdownItem
              onClick={() => setSettingOpen(true)}
              className="py-2 px-4 "
              key="setting"
              startContent={<AiOutlineSetting size={20} />}
            >
              Settings
            </DropdownItem>
          </DropdownSection>
          <DropdownSection className="mb-0">
            {isGuest ? (
              <DropdownItem
                onClick={() => setAuthOpen(true)}
                className="py-2 px-4"
                key="login"
                startContent={<IoMdLogIn size={20} />}
              >
                Login
              </DropdownItem>
            ) : (
              <DropdownItem
                onClick={handleLogout}
                className="py-2 px-4"
                key="logout"
                startContent={<IoMdLogOut size={20} />}
              >
                Logout
              </DropdownItem>
            )}
          </DropdownSection>
        </DropdownMenu>
      </Dropdown>
    </div>
  );
}

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

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    const data = parseJwt(localStorage.getItem("token") || "");
    if (data.username) {
      setUsername(data.username);
      setAvatarUrl(data.avatar_url);
    }
    if (data.provider) {
      setIsGuest(false);
    }

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
                onOpenChange={onAuthModalOpenChange}
              />
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
