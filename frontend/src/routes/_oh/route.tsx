import React from "react";
import { useRouteError, isRouteErrorResponse, Outlet } from "react-router";
import i18n from "#/i18n";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useAuth } from "#/context/auth-context";
import { useUserPrefs } from "#/context/user-prefs-context";
import { useConfig } from "#/hooks/query/use-config";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { WaitlistModal } from "#/components/features/waitlist/waitlist-modal";
import { AnalyticsConsentFormModal } from "#/components/features/analytics/analytics-consent-form-modal";
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";

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

export default function MainApp() {
  const { gitHubToken, clearToken } = useAuth();
  const { settings } = useUserPrefs();

  const [consentFormIsOpen, setConsentFormIsOpen] = React.useState(
    !localStorage.getItem("analytics-consent"),
  );

  const config = useConfig();
  const {
    data: isAuthed,
    isFetched,
    isFetching: isFetchingAuth,
  } = useIsAuthed();

  const gitHubAuthUrl = useGitHubAuthUrl({
    gitHubToken,
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  React.useEffect(() => {
    if (isFetched && !isAuthed) clearToken();
  }, [isFetched, isAuthed]);

  React.useEffect(() => {
    if (settings.LANGUAGE) {
      i18n.changeLanguage(settings.LANGUAGE);
    }
  }, [settings.LANGUAGE]);

  const isInWaitlist =
    !isFetchingAuth && !isAuthed && config.data?.APP_MODE === "saas";

  const { settingsAreUpToDate } = useUserPrefs();
  const [showAIConfig, setShowAIConfig] = React.useState(true);

  return (
    <div
      data-testid="root-layout"
      className="bg-root-primary p-3 h-screen md:min-w-[1024px] overflow-x-hidden flex flex-col md:flex-row gap-3"
    >
      <Sidebar />

      <div className="h-[calc(100%-50px)] md:h-full w-full relative">
        <Outlet />
      </div>

      {isInWaitlist && (
        <WaitlistModal ghToken={gitHubToken} githubAuthUrl={gitHubAuthUrl} />
      )}

      {config.data?.APP_MODE === "oss" && consentFormIsOpen && (
        <AnalyticsConsentFormModal
          onClose={() => setConsentFormIsOpen(false)}
        />
      )}

      {(isAuthed || !settingsAreUpToDate) && showAIConfig && (
        <SettingsModal onClose={() => setShowAIConfig(false)} />
      )}
    </div>
  );
}
