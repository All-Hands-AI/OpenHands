import React from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  useNavigate,
  useLocation,
  useNavigation,
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
import { useAutoLogin } from "#/hooks/use-auto-login";
import { useAuthCallback } from "#/hooks/use-auth-callback";
import { LOCAL_STORAGE_KEYS } from "#/utils/local-storage";
import { EmailVerificationGuard } from "#/components/features/guards/email-verification-guard";
import { MaintenanceBanner } from "#/components/features/maintenance/maintenance-banner";
import { LoadingOverlay } from "#/components/shared/loading-overlay";

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

export default function RootLayout() {
  const navigation = useNavigation();
  const location = useLocation();
  const [isNavigating, setIsNavigating] = useState(false);
  const config = useConfig();
  const balance = useBalance();
  const settings = useSettings();

  useEffect(() => {
    if (navigation.state !== "idle") {
      setIsNavigating(true);
    } else {
      const id = setTimeout(() => setIsNavigating(false), 150);
      return () => clearTimeout(id);
    }
  }, [navigation.state, location.pathname]);

  const showGlobalLoader = useMemo(() => {
    const isFetchingAuth = false; // plug actual auth query if available
    const isFetchingSettings = settings.isFetching;
    const isFetchingBalance = balance.isFetching;
    return (
      isNavigating || isFetchingAuth || isFetchingSettings || isFetchingBalance || config.isLoading
    );
  }, [isNavigating, settings.isFetching, balance.isFetching, config.isLoading]);

  const loaderMessage = isNavigating ? "Loading..." : (settings.isFetching ? "Loading settings..." : undefined);

  return (
    <div className="h-full w-full">
      <LoadingOverlay visible={showGlobalLoader} message={loaderMessage} />
      <Outlet />
    </div>
  );
}
