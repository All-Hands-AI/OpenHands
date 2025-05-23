import React from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  useNavigate,
  useLocation,
} from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import i18n from "#/i18n";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useConfig } from "#/hooks/query/use-config";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { AuthModal } from "#/components/features/waitlist/auth-modal";
import { ReauthModal } from "#/components/features/waitlist/reauth-modal";
import { AnalyticsConsentFormModal } from "#/components/features/analytics/analytics-consent-form-modal";
import { useSettings } from "#/hooks/query/use-settings";
import { useMigrateUserConsent } from "#/hooks/use-migrate-user-consent";
import { useBalance } from "#/hooks/query/use-balance";
import { SetupPaymentModal } from "#/components/features/payment/setup-payment-modal";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";
import { useTrackLastPage } from "#/hooks/use-track-last-page";
import { useAutoLogin } from "#/hooks/use-auto-login";
import { LOCAL_STORAGE_KEYS } from "#/utils/local-storage";

export function ErrorBoundary() {
  const error = useRouteError();
  const { t } = useTranslation();

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
        <h1>{t(I18nKey.ERROR$GENERIC)}</h1>
        <pre>{error.message}</pre>
      </div>
    );
  }

  return (
    <div>
      <h1>{t(I18nKey.ERROR$UNKNOWN)}</h1>
    </div>
  );
}

export default function MainApp() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isOnTosPage = useIsOnTosPage();
  const { data: settings } = useSettings();
  const { error } = useBalance();
  const { migrateUserConsent } = useMigrateUserConsent();
  const { t } = useTranslation();

  const config = useConfig();
  const {
    data: isAuthed,
    isFetching: isFetchingAuth,
    isError: isAuthError,
  } = useIsAuthed();

  // Always call the hook, but we'll only use the result when not on TOS page
  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  // When on TOS page, we don't use the GitHub auth URL
  const effectiveGitHubAuthUrl = isOnTosPage ? null : gitHubAuthUrl;

  const [consentFormIsOpen, setConsentFormIsOpen] = React.useState(false);

  // Track the last visited page
  useTrackLastPage();

  // Auto-login if login method is stored in local storage
  useAutoLogin();

  React.useEffect(() => {
    // Don't change language when on TOS page
    if (!isOnTosPage && settings?.LANGUAGE) {
      i18n.changeLanguage(settings.LANGUAGE);
    }
  }, [settings?.LANGUAGE, isOnTosPage]);

  React.useEffect(() => {
    // Don't show consent form when on TOS page
    if (!isOnTosPage) {
      const consentFormModalIsOpen =
        settings?.USER_CONSENTS_TO_ANALYTICS === null;

      setConsentFormIsOpen(consentFormModalIsOpen);
    }
  }, [settings, isOnTosPage]);

  React.useEffect(() => {
    // Don't migrate user consent when on TOS page
    if (!isOnTosPage) {
      // Migrate user consent to the server if it was previously stored in localStorage
      migrateUserConsent({
        handleAnalyticsWasPresentInLocalStorage: () => {
          setConsentFormIsOpen(false);
        },
      });
    }
  }, [isOnTosPage]);

  React.useEffect(() => {
    if (settings?.IS_NEW_USER && config.data?.APP_MODE === "saas") {
      displaySuccessToast(t(I18nKey.BILLING$YOURE_IN));
    }
  }, [settings?.IS_NEW_USER, config.data?.APP_MODE]);

  React.useEffect(() => {
    // Don't do any redirects when on TOS page
    // Don't allow users to use the app if it 402s
    if (!isOnTosPage && error?.status === 402) {
      navigate("/");
    }
  }, [error?.status, pathname, isOnTosPage]);

  // Check if login method exists in local storage
  const loginMethodExists = React.useMemo(() => {
    // Only check localStorage if we're in a browser environment
    if (typeof window !== "undefined" && window.localStorage) {
      return localStorage.getItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD) !== null;
    }
    return false;
  }, []);

  const renderAuthModal =
    !isAuthed &&
    !isAuthError &&
    !isFetchingAuth &&
    !isOnTosPage &&
    config.data?.APP_MODE === "saas" &&
    !loginMethodExists; // Don't show auth modal if login method exists in local storage

  const renderReAuthModal =
    !isAuthed &&
    !isAuthError &&
    !isFetchingAuth &&
    !isOnTosPage &&
    config.data?.APP_MODE === "saas" &&
    loginMethodExists;

  return (
    <div
      data-testid="root-layout"
      className="bg-base p-3 h-screen md:min-w-[1024px] flex flex-col md:flex-row gap-3"
    >
      <Sidebar />

      <div
        id="root-outlet"
        className="h-[calc(100%-50px)] md:h-full w-full relative overflow-auto"
      >
        <Outlet />
      </div>

      {renderAuthModal && (
        <AuthModal
          githubAuthUrl={effectiveGitHubAuthUrl}
          appMode={config.data?.APP_MODE}
        />
      )}
      {renderReAuthModal && <ReauthModal />}
      {config.data?.APP_MODE === "oss" && consentFormIsOpen && (
        <AnalyticsConsentFormModal
          onClose={() => {
            setConsentFormIsOpen(false);
          }}
        />
      )}

      {config.data?.FEATURE_FLAGS.ENABLE_BILLING &&
        config.data?.APP_MODE === "saas" &&
        settings?.IS_NEW_USER && <SetupPaymentModal />}
    </div>
  );
}
