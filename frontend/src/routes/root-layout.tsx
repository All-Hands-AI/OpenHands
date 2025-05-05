import React from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  useNavigate,
  useLocation,
  useSearchParams,
} from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import i18n from "#/i18n";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useConfig } from "#/hooks/query/use-config";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { AuthModal } from "#/components/features/waitlist/auth-modal";
import { AnalyticsConsentFormModal } from "#/components/features/analytics/analytics-consent-form-modal";
import { useSettings } from "#/hooks/query/use-settings";
import { useMigrateUserConsent } from "#/hooks/use-migrate-user-consent";
import { useBalance } from "#/hooks/query/use-balance";
import { SetupPaymentModal } from "#/components/features/payment/setup-payment-modal";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";

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
  const tosPageStatus = useIsOnTosPage();
  const [searchParams] = useSearchParams();
  const { data: settings } = useSettings();
  const { error, isFetching } = useBalance();
  const { migrateUserConsent } = useMigrateUserConsent();
  const { t } = useTranslation();

  const config = useConfig();
  const {
    data: isAuthed,
    isFetching: isFetchingAuth,
    isError: authError,
  } = useIsAuthed();

  // Always call the hook, but we'll only use the result when not on TOS page
  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  // When on TOS page, we don't use the GitHub auth URL
  const effectiveGitHubAuthUrl = tosPageStatus ? null : gitHubAuthUrl;

  const [consentFormIsOpen, setConsentFormIsOpen] = React.useState(false);

  React.useEffect(() => {
    // Don't change language when on TOS page
    if (!tosPageStatus && settings?.LANGUAGE) {
      i18n.changeLanguage(settings.LANGUAGE);
    }
  }, [settings?.LANGUAGE, tosPageStatus]);

  React.useEffect(() => {
    // Don't show consent form when on TOS page
    if (!tosPageStatus) {
      const consentFormModalIsOpen =
        settings?.USER_CONSENTS_TO_ANALYTICS === null;

      setConsentFormIsOpen(consentFormModalIsOpen);
    }
  }, [settings, tosPageStatus]);

  React.useEffect(() => {
    // Don't migrate user consent when on TOS page
    if (!tosPageStatus) {
      // Migrate user consent to the server if it was previously stored in localStorage
      migrateUserConsent({
        handleAnalyticsWasPresentInLocalStorage: () => {
          setConsentFormIsOpen(false);
        },
      });
    }
  }, [tosPageStatus]);

  React.useEffect(() => {
    // Don't do any redirects when on TOS page
    if (!tosPageStatus) {
      // Don't allow users to use the app if it 402s
      if (error?.status === 402 && pathname !== "/") {
        navigate("/");
      } else if (
        !isFetching &&
        searchParams.get("free_credits") === "success"
      ) {
        displaySuccessToast(t(I18nKey.BILLING$YOURE_IN));
        searchParams.delete("free_credits");
        navigate("/");
      }
    }
  }, [error?.status, pathname, isFetching, tosPageStatus]);

  // When on TOS page, we don't make any API calls, so we need to handle this case
  const userIsAuthed = tosPageStatus ? false : !!isAuthed && !authError;

  // Only show the auth modal if:
  // 1. User is not authenticated
  // 2. We're not currently on the TOS page
  // 3. We're in SaaS mode
  const renderAuthModal =
    !isFetchingAuth &&
    !userIsAuthed &&
    !tosPageStatus &&
    config.data?.APP_MODE === "saas";

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
