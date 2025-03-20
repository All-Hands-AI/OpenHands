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
import i18n from "#/i18n";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useConfig } from "#/hooks/query/use-config";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { WaitlistModal } from "#/components/features/waitlist/waitlist-modal";
import { AnalyticsConsentFormModal } from "#/components/features/analytics/analytics-consent-form-modal";
import { useSettings } from "#/hooks/query/use-settings";
import { useAuth } from "#/context/auth-context";
import { useMigrateUserConsent } from "#/hooks/use-migrate-user-consent";
import { useBalance } from "#/hooks/query/use-balance";
import { SetupPaymentModal } from "#/components/features/payment/setup-payment-modal";
import { BILLING_SETTINGS } from "#/utils/feature-flags";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";

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
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [searchParams] = useSearchParams();
  const { githubTokenIsSet } = useAuth();
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

  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  const [consentFormIsOpen, setConsentFormIsOpen] = React.useState(false);

  React.useEffect(() => {
    if (settings?.LANGUAGE) {
      i18n.changeLanguage(settings.LANGUAGE);
    }
  }, [settings?.LANGUAGE]);

  React.useEffect(() => {
    const consentFormModalIsOpen =
      settings?.USER_CONSENTS_TO_ANALYTICS === null;

    setConsentFormIsOpen(consentFormModalIsOpen);
  }, [settings]);

  React.useEffect(() => {
    // Migrate user consent to the server if it was previously stored in localStorage
    migrateUserConsent({
      handleAnalyticsWasPresentInLocalStorage: () => {
        setConsentFormIsOpen(false);
      },
    });
  }, []);

  React.useEffect(() => {
    // Don't allow users to use the app if it 402s
    if (error?.status === 402 && pathname !== "/") {
      navigate("/");
    } else if (!isFetching && searchParams.get("free_credits") === "success") {
      displaySuccessToast(t("BILLING$YOURE_IN"));
      searchParams.delete("free_credits");
      navigate("/");
    }
  }, [error?.status, pathname, isFetching]);

  const userIsAuthed = !!isAuthed && !authError;
  const renderWaitlistModal =
    !isFetchingAuth && !userIsAuthed && config.data?.APP_MODE === "saas";

  return (
    <div
      data-testid="root-layout"
      className="bg-base p-3 h-screen md:min-w-[1024px] overflow-x-hidden flex flex-col md:flex-row gap-3"
    >
      <Sidebar />

      <div
        id="root-outlet"
        className="h-[calc(100%-50px)] md:h-full w-full relative"
      >
        <Outlet />
      </div>

      {renderWaitlistModal && (
        <WaitlistModal
          ghTokenIsSet={githubTokenIsSet}
          githubAuthUrl={gitHubAuthUrl}
        />
      )}

      {config.data?.APP_MODE === "oss" && consentFormIsOpen && (
        <AnalyticsConsentFormModal
          onClose={() => {
            setConsentFormIsOpen(false);
          }}
        />
      )}

      {BILLING_SETTINGS() &&
        config.data?.APP_MODE === "saas" &&
        settings?.IS_NEW_USER && <SetupPaymentModal />}
    </div>
  );
}
