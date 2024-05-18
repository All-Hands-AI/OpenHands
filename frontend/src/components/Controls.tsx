import {
  Dropdown,
  DropdownItem,
  DropdownMenu,
  DropdownSection,
  DropdownTrigger,
  User,
} from "@nextui-org/react";
import { AiOutlineSetting } from "react-icons/ai";
import { IoMdLogIn, IoMdLogOut } from "react-icons/io";
import React from "react";
import AgentStatusBar from "#/components/AgentStatusBar";
import AgentControlBar from "#/components/AgentControlBar";

interface ControlProps {
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
}: ControlProps): JSX.Element {
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

export default Controls;
