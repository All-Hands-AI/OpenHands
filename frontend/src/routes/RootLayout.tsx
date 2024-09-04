import React from "react";
import {
  ActionFunctionArgs,
  json,
  Link,
  Outlet,
  redirect,
  useLoaderData,
} from "react-router-dom";
import { useDisclosure } from "@nextui-org/react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ghClient } from "#/api/github";
import CogTooth from "#/assets/cog-tooth";
import { SettingsForm } from "./SettingsForm";
import { getSettings, Settings } from "#/services/settings";
import ConnectToGitHubByTokenModal from "#/components/modals/ConnectToGitHubByTokenModal";

interface ModalBackdropProps {
  children: React.ReactNode;
}

function ModalBackdrop({ children }: ModalBackdropProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div onClick={(e) => e.stopPropagation()} className="relative">
        {children}
      </div>
    </div>
  );
}

const getModels = async () => {
  try {
    const response = await fetch("/api/options/models");
    return await response.json();
  } catch (error) {
    return ["openai/gpt-4o", "openai/gpt-3.5-turbo"];
  }
};

const getAgents = async () => {
  try {
    const response = await fetch("/api/options/agents");
    return await response.json();
  } catch (error) {
    return ["CodeActAgent", "MonologueAgent", "DummyAgent"];
  }
};

type LoaderReturnType = {
  user: GitHubUser | null;
  models: string[];
  agents: string[];
  settings: Settings;
  TOS: string | null;
};

export const loader = async () => {
  redirect("/home");
  let user: GitHubUser | null = null;

  try {
    user = await ghClient.getUser();
  } catch (error) {
    console.error("Failed to fetch user");
  }

  const models = await getModels();
  const agents = await getAgents();
  const settings = getSettings();

  const TOS = localStorage.getItem("TOS");

  return json({ user, models, agents, settings, TOS });
};

type ActionReturnType = {
  status: "success" | "error";
  message?: string;
};

export const action = async ({ request }: ActionFunctionArgs) => {
  const formData = await request.formData();
  const tos = formData.get("tos")?.toString();

  if (!tos)
    return json({
      status: "error",
      message: "You must agree to the terms of service",
    });
  localStorage.setItem("TOS", "true");

  const token = formData.get("token")?.toString();
  if (token) localStorage.setItem("GITHUB_TOKEN", token);

  return json({ status: "success" });
};

function RootLayout() {
  const { user, models, agents, settings, TOS } =
    useLoaderData() as LoaderReturnType;

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
            src={user?.avatar_url}
            alt={`${user?.login} avatar`}
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
      <div className="w-full relative">
        <Outlet />
        {!TOS && (
          <ModalBackdrop>
            <ConnectToGitHubByTokenModal />
          </ModalBackdrop>
        )}
        {settingsModalIsOpen && (
          <div className="absolute top-1/2 right-1/2 transform translate-x-1/2 -translate-y-1/2">
            <div className="bg-root-primary w-[384px] p-6 rounded-xl flex flex-col gap-2">
              <span className="text-xl leading-6 font-semibold -tracking-[0.01em">
                AI Provider Configuration
              </span>
              <p className="text-xs text-[#A3A3A3]">
                To continue, connect an OpenAI, Anthropic, or other LLM account
              </p>
              <SettingsForm
                settings={settings}
                models={models}
                agents={agents}
                onClose={onSettingsModalOpenChange}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RootLayout;
