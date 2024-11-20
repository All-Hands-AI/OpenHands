import React from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  useLocation,
  Outlet,
  useNavigate,
} from "@remix-run/react";
import { useDispatch } from "react-redux";
import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import CogTooth from "#/assets/cog-tooth";
import { SettingsForm } from "#/components/form/settings-form";
import AccountSettingsModal from "#/components/modals/AccountSettingsModal";
import { DangerModal } from "#/components/modals/confirmation-modals/danger-modal";
import { LoadingSpinner } from "#/components/modals/LoadingProject";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { UserActions } from "#/components/user-actions";
import i18n from "#/i18n";
import { getSettings, settingsAreUpToDate } from "#/services/settings";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import NewProjectIcon from "#/icons/new-project.svg?react";
import DocsIcon from "#/icons/docs.svg?react";
import { userIsAuthenticated } from "#/utils/user-is-authenticated";
import { WaitlistModal } from "#/components/waitlist-modal";
import { AnalyticsConsentFormModal } from "#/components/analytics-consent-form-modal";
import { setCurrentAgentState } from "#/state/agentSlice";
import AgentState from "#/types/AgentState";
import { useConfig } from "#/hooks/query/use-config";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { getGitHubToken, getToken } from "#/services/auth";
import { logoutCleanup } from "#/utils/logout-cleanup";
import { clearSession } from "#/utils/clear-session";

export function ErrorBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
        <pre>
          {error.data instanceof Object
            ? JSON.stringify(error.data)
            : error.data}
        </pre>
      </div>
    );
  }
  if (error instanceof Error) {
    return (
      <div>
        <h1>Uh oh, an error occurred!</h1>
        <pre>{error.message}</pre>
      </div>
    );
  }

  return (
    <div>
      <h1>Uh oh, an unknown error occurred!</h1>
    </div>
  );
}

const fetchAiConfigOptions = async () => ({
  models: await OpenHands.getModels(),
  agents: await OpenHands.getAgents(),
  securityAnalyzers: await OpenHands.getSecurityAnalyzers(),
});

export default function MainApp() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();

  const { token, ghToken, settingsIsUpdated, settings, analyticsConsent } = {
    token: getToken(),
    ghToken: getGitHubToken(),
    settingsIsUpdated: settingsAreUpToDate(),
    settings: getSettings(),
    analyticsConsent: localStorage.getItem("analytics-consent"),
  };

  const [accountSettingsModalOpen, setAccountSettingsModalOpen] =
    React.useState(false);
  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [startNewProjectModalIsOpen, setStartNewProjectModalIsOpen] =
    React.useState(false);
  const [consentFormIsOpen, setConsentFormIsOpen] = React.useState(
    !localStorage.getItem("analytics-consent"),
  );

  const config = useConfig();
  const user = useGitHubUser(ghToken);
  const { data: isAuthed } = useQuery({
    queryKey: ["user", "authenticated", ghToken],
    queryFn: userIsAuthenticated,
  });
  const aiConfigOptions = useQuery({
    queryKey: ["ai-config-options"],
    queryFn: fetchAiConfigOptions,
  });

  const gitHubAuthUrl = useGitHubAuthUrl({
    gitHubToken: ghToken,
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  React.useEffect(() => {
    if (!isAuthed) localStorage.removeItem("token");
  }, [isAuthed]);

  React.useEffect(() => {
    // i18n.language
    if (settings.LANGUAGE) {
      i18n.changeLanguage(settings.LANGUAGE);
    }
  }, [settings.LANGUAGE]);

  React.useEffect(() => {
    // If the github token is invalid, open the account settings modal again
    if (user.isError) {
      setAccountSettingsModalOpen(true);
    }
  }, [user.isError]);

  const handleAccountSettingsModalClose = () => {
    // If the user closes the modal without connecting to GitHub,
    // we need to log them out to clear the invalid token from the
    // local storage
    if (user.isError) logoutCleanup();
    setAccountSettingsModalOpen(false);
  };

  const handleEndSession = () => {
    setStartNewProjectModalIsOpen(false);
    dispatch(setCurrentAgentState(AgentState.LOADING));
    clearSession();
    navigate("/");
  };

  return (
    <div
      data-testid="root-layout"
      className="bg-root-primary p-3 h-screen min-w-[1024px] overflow-x-hidden flex gap-3"
    >
      <aside className="px-1 flex flex-col gap-1">
        <div className="w-[34px] h-[34px] flex items-center justify-center">
          {user.isLoading && <LoadingSpinner size="small" />}
          {!user.isLoading && (
            <button
              type="button"
              aria-label="All Hands Logo"
              onClick={() => {
                if (location.pathname.startsWith("/app"))
                  setStartNewProjectModalIsOpen(true);
              }}
            >
              <AllHandsLogo width={34} height={23} />
            </button>
          )}
        </div>
        <nav className="py-[18px] flex flex-col items-center gap-[18px]">
          <UserActions
            user={user.data ? { avatar_url: user.data.avatar_url } : undefined}
            onLogout={logoutCleanup}
            onClickAccountSettings={() => setAccountSettingsModalOpen(true)}
          />
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
            <DocsIcon width={28} height={28} />
          </a>
          {!!token && (
            <button
              data-testid="new-project-button"
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
      </div>

      {isAuthed && (!settingsIsUpdated || settingsModalIsOpen) && (
        <ModalBackdrop onClose={() => setSettingsModalIsOpen(false)}>
          <div
            data-testid="ai-config-modal"
            className="bg-root-primary w-[384px] p-6 rounded-xl flex flex-col gap-2"
          >
            {aiConfigOptions.error && (
              <p className="text-danger text-xs">
                {aiConfigOptions.error.message}
              </p>
            )}
            <span className="text-xl leading-6 font-semibold -tracking-[0.01em">
              AI Provider Configuration
            </span>
            <p className="text-xs text-[#A3A3A3]">
              To continue, connect an OpenAI, Anthropic, or other LLM account
            </p>
            <p className="text-xs text-danger">
              Changing settings during an active session will end the session
            </p>
            {aiConfigOptions.isLoading && (
              <div className="flex justify-center">
                <LoadingSpinner size="small" />
              </div>
            )}
            {aiConfigOptions.data && (
              <SettingsForm
                settings={settings}
                models={aiConfigOptions.data?.models}
                agents={aiConfigOptions.data?.agents}
                securityAnalyzers={aiConfigOptions.data?.securityAnalyzers}
                onClose={() => {
                  setSettingsModalIsOpen(false);
                }}
              />
            )}
          </div>
        </ModalBackdrop>
      )}
      {accountSettingsModalOpen && (
        <ModalBackdrop onClose={handleAccountSettingsModalClose}>
          <AccountSettingsModal
            onClose={handleAccountSettingsModalClose}
            selectedLanguage={settings.LANGUAGE}
            gitHubError={user.isError}
            analyticsConsent={analyticsConsent}
          />
        </ModalBackdrop>
      )}
      {startNewProjectModalIsOpen && (
        <ModalBackdrop onClose={() => setStartNewProjectModalIsOpen(false)}>
          <DangerModal
            title="Are you sure you want to exit?"
            description="You will lose any unsaved information."
            buttons={{
              danger: {
                text: "Exit Project",
                onClick: handleEndSession,
              },
              cancel: {
                text: "Cancel",
                onClick: () => setStartNewProjectModalIsOpen(false),
              },
            }}
          />
        </ModalBackdrop>
      )}
      {!isAuthed && config.data?.APP_MODE === "saas" && (
        <WaitlistModal ghToken={ghToken} githubAuthUrl={gitHubAuthUrl} />
      )}
      {consentFormIsOpen && (
        <AnalyticsConsentFormModal
          onClose={() => setConsentFormIsOpen(false)}
        />
      )}
    </div>
  );
}
