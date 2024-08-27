import React from "react";
import { json, Link, Outlet, useLoaderData } from "react-router-dom";
import { useDisclosure } from "@nextui-org/react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ghClient } from "#/api/github";
import SettingsModal from "#/components/modals/settings/SettingsModal";
import CogTooth from "#/assets/cog-tooth";

type LoaderReturnType = {
  user: GitHubUser;
};

export const loader = async () => {
  const user = await ghClient.getUser();
  return json({ user });
};

function RootLayout() {
  const { user } = useLoaderData() as LoaderReturnType;

  const {
    isOpen: settingsModalIsOpen,
    onOpen: onSettingsModalOpen,
    onOpenChange: onSettingsModalOpenChange,
  } = useDisclosure();

  return (
    <div className="bg-root-primary p-3 h-screen flex gap-3">
      <aside className="px-1 flex flex-col gap-[15px]">
        <Link to="/">
          <AllHandsLogo width={34} height={23} />
        </Link>
        <nav className="py-[18px] flex flex-col items-center gap-[18px]">
          <img
            src={user.avatar_url}
            alt={`${user.login} avatar`}
            className="w-8 h-8 rounded-full"
          />
          <button
            type="button"
            className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
            onClick={onSettingsModalOpen}
            aria-label="Settings"
          >
            <CogTooth />
          </button>
          <div className="w-8 h-8 rounded-full bg-green-100" />
          <div className="w-8 h-8 rounded-full bg-blue-100" />
        </nav>
      </aside>
      <div className="w-full">
        <Outlet />
        <SettingsModal
          isOpen={settingsModalIsOpen}
          onOpenChange={onSettingsModalOpenChange}
        />
      </div>
    </div>
  );
}

export default RootLayout;
