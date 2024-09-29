import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  defer,
  useFetcher,
  useLoaderData,
  useLocation,
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
import {
  getAgents,
  getModels,
  retrieveSecurityAnalyzers,
} from "./api/open-hands";
import LoadingProjectModal, {
  LoadingSpinner,
} from "./components/modals/LoadingProject";
import {
  getSettings,
  maybeMigrateSettings,
  settingsAreUpToDate,
} from "./services/settings";
import AccountSettingsModal from "./components/modals/AccountSettingsModal";
import NewProjectIcon from "./assets/new-project.svg?react";
import ConfirmResetWorkspaceModal from "./components/modals/confirmation-modals/ConfirmResetWorkspaceModal";
import DefaultUserAvatar from "./assets/default-user.svg?react";
import i18n from "./i18n";
import { cn } from "./utils/utils";
import { AccountSettingsContextMenu } from "./components/account-settings-context-menu";

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

  const models = getModels();
  const agents = getAgents();
  const securityAnalyzers = retrieveSecurityAnalyzers();

  let user: GitHubUser | GitHubErrorReponse | null = null;
  if (ghToken) user = await retrieveGitHubUser(ghToken);

  let settingsIsUpdated = false;
  if (!settingsAreUpToDate()) {
    maybeMigrateSettings();
    settingsIsUpdated = true;
  }

  const settings = getSettings();
  await i18n.changeLanguage(settings.LANGUAGE);

  return defer({
    token,
    ghToken,
    user,
    models,
    agents,
    securityAnalyzers,
    settingsIsUpdated,
    settings,
  });
};

export default function App() {
  const navigation = useNavigation();
  const location = useLocation();
  const fetcher = useFetcher({ key: "login" });
  const {
    token,
    user,
    models,
    agents,
    securityAnalyzers,
    settingsIsUpdated,
    settings,
  } = useLoaderData<typeof clientLoader>();
  const submit = useSubmit();
  const logoutFetcher = useFetcher({ key: "logout" });

  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);
  const [accountSettingsModalOpen, setAccountSettingsModalOpen] =
    React.useState(false);
  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [startNewProjectModalIsOpen, setStartNewProjectModalIsOpen] =
    React.useState(false);

  React.useEffect(() => {
    if (isGitHubErrorReponse(user)) {
      setAccountSettingsModalOpen(true);
    }
  }, [user]);

  return (
    <div className="bg-root-primary p-3 h-screen flex gap-3">
      <aside className="px-1 flex flex-col gap-[15px]">
        <button
          type="button"
          aria-label="All Hands Logo"
          onClick={() => setStartNewProjectModalIsOpen(true)}
        >
          <AllHandsLogo width={34} height={23} />
        </button>
        <nav className="py-[18px] flex flex-col items-center gap-[18px]">
          <div className="w-8 h-8 relative">
            <button
              type="button"
              className={cn(
                "bg-white w-8 h-8 rounded-full flex items-center justify-center",
                fetcher.state !== "idle" && "bg-transparent",
              )}
              onClick={() => {
                if (!user) {
                  // If the user is not logged in, opening the modal is the only option,
                  // so we do that instead of toggling the context menu.
                  setAccountSettingsModalOpen(true);
                  return;
                }
                setAccountContextMenuIsVisible((prev) => !prev);
              }}
            >
              {!user && fetcher.state === "idle" && (
                <DefaultUserAvatar width={20} height={20} />
              )}
              {!user && fetcher.state !== "idle" && (
                <LoadingSpinner size="small" />
              )}
              {user && !isGitHubErrorReponse(user) && (
                <img
                  src={user.avatar_url}
                  alt="User avatar"
                  className="w-full h-full rounded-full"
                />
              )}
            </button>
            {accountContextMenuIsVisible && (
              <AccountSettingsContextMenu
                isLoggedIn={!!user}
                onClose={() => setAccountContextMenuIsVisible(false)}
                onClickAccountSettings={() => {
                  setAccountContextMenuIsVisible(false);
                  setAccountSettingsModalOpen(true);
                }}
                onLogout={() => {
                  logoutFetcher.submit(
                    {},
                    {
                      method: "POST",
                      action: "/logout",
                    },
                  );
                  setAccountContextMenuIsVisible(false);
                }}
              />
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
          <a
            href="https://docs.all-hands.dev"
            target="_blank"
            rel="noreferrer noopener"
            className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
            aria-label="Documentation"
          >
            Docs
          </a>
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
      <div className="h-full w-full relative">
        <Outlet />
        {navigation.state === "loading" && location.pathname !== "/" && (
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
                securityAnalyzers={securityAnalyzers}
                onClose={() => setSettingsModalIsOpen(false)}
              />
            </div>
          </ModalBackdrop>
        )}
        {accountSettingsModalOpen && (
          <ModalBackdrop>
            <AccountSettingsModal
              onClose={() => setAccountSettingsModalOpen(false)}
              selectedLanguage={settings.LANGUAGE}
              gitHubError={isGitHubErrorReponse(user)}
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
                  replace: true,
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
