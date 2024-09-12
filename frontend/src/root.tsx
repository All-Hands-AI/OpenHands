import {
  ClientActionFunctionArgs,
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  defer,
  json,
  useLoaderData,
  useNavigation,
  useSubmit,
} from "@remix-run/react";
import "./tailwind.css";
import "./index.css";
import React from "react";
import CogTooth from "./assets/cog-tooth";
import { SettingsForm } from "./components/form/settings-form";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { isGitHubErrorReponse, retrieveGitHubUser } from "./api/github";
import { getAgents, getModels } from "./api/open-hands";
import LoadingProjectModal from "./components/modals/LoadingProject";
import { getSettings } from "./services/settings";
import { ContextMenu } from "./components/context-menu/context-menu";
import { ContextMenuListItem } from "./components/context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "./components/context-menu/context-menu-separator";
import AccountSettingsModal from "./components/modals/AccountSettingsModal";
import NewProjectIcon from "./assets/new-project.svg?react";
import ConfirmResetWorkspaceModal from "./components/modals/confirmation-modals/ConfirmResetWorkspaceModal";
import DefaultUserAvatar from "./assets/default-user.svg?react";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export const clientLoader = async () => {
  const token = localStorage.getItem("token");
  const ghToken = localStorage.getItem("ghToken");
  const settingsVersion = localStorage.getItem("SETTINGS_VERSION");

  const models = getModels();
  const agents = getAgents();

  let user: GitHubUser | null = null;
  if (ghToken) {
    const data = await retrieveGitHubUser(ghToken);
    if (!isGitHubErrorReponse(data)) user = data;
  }

  let settingsIsUpdated = false;
  if (settingsVersion !== import.meta.env.VITE_SETTINGS_VERSION) {
    settingsIsUpdated = true;
  }

  return defer({
    token,
    ghToken,
    user,
    models,
    agents,
    settingsIsUpdated,
    settings: getSettings(),
  });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const ghToken = formData.get("ghToken")?.toString();

  if (ghToken) {
    localStorage.setItem("ghToken", ghToken);
  }

  return json({ success: true });
};

export default function App() {
  const navigation = useNavigation();
  const { token, user, models, agents, settingsIsUpdated, settings } =
    useLoaderData<typeof clientLoader>();
  const submit = useSubmit();

  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);
  const [accountSettingsModalOpen, setAccountSettingsModalOpen] =
    React.useState(false);
  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [startNewProjectModalIsOpen, setStartNewProjectModalIsOpen] =
    React.useState(false);

  return (
    <div className="bg-root-primary p-3 h-screen flex gap-3">
      <aside className="px-1 flex flex-col gap-[15px]">
        <Link data-testid="link-to-main" to="/">
          <AllHandsLogo width={34} height={23} />
        </Link>
        <nav className="py-[18px] flex flex-col items-center gap-[18px]">
          <div className="w-8 h-8 relative">
            <button
              type="button"
              className="bg-white w-8 h-8 rounded-full flex items-center justify-center"
              onClick={() => setAccountContextMenuIsVisible((prev) => !prev)}
            >
              {!user && <DefaultUserAvatar width={20} height={20} />}
              {user && (
                <img
                  src={user.avatar_url}
                  alt="User avatar"
                  className="w-full h-full rounded-full"
                />
              )}
            </button>

            {accountContextMenuIsVisible && (
              <ContextMenu className="absolute left-full -top-1 z-10">
                <ContextMenuListItem
                  onClick={() => {
                    setAccountContextMenuIsVisible(false);
                    setAccountSettingsModalOpen(true);
                  }}
                >
                  Account Settings
                </ContextMenuListItem>
                <ContextMenuListItem>Documentation</ContextMenuListItem>
                <ContextMenuSeparator />
                <ContextMenuListItem>Logout</ContextMenuListItem>
              </ContextMenu>
            )}
          </div>
          <button
            type="button"
            className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
            onClick={() => setSettingsModalIsOpen(true)}
            aria-label="Settings"
          >
            <CogTooth />
          </button>
          {!!token && (
            <button
              type="button"
              aria-label="Start new project"
              onClick={() => setStartNewProjectModalIsOpen(true)}
            >
              <NewProjectIcon width={28} height={28} />
            </button>
          )}
        </nav>
      </aside>
      <div className="w-full relative">
        <Outlet />
        {navigation.state === "loading" && (
          <ModalBackdrop>
            <LoadingProjectModal />
          </ModalBackdrop>
        )}
        {(settingsIsUpdated || settingsModalIsOpen) && (
          <ModalBackdrop>
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
                onClose={() => setSettingsModalIsOpen(false)}
              />
            </div>
          </ModalBackdrop>
        )}
        {accountSettingsModalOpen && (
          <ModalBackdrop>
            <AccountSettingsModal
              onClose={() => setAccountSettingsModalOpen(false)}
              language={settings.LANGUAGE}
            />
          </ModalBackdrop>
        )}
        {startNewProjectModalIsOpen && (
          <ModalBackdrop>
            <ConfirmResetWorkspaceModal
              onConfirm={() => {
                setStartNewProjectModalIsOpen(false);

                // remove token action and redirect to /
                submit(new FormData(), {
                  method: "POST",
                  action: "/new-session",
                });
              }}
              onCancel={() => setStartNewProjectModalIsOpen(false)}
            />
          </ModalBackdrop>
        )}
      </div>
    </div>
  );
}

export function HydrateFallback() {
  return <p>Loading...</p>;
}
