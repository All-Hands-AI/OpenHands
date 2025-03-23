import React from "react";
import { generateGitHubAuthUrl } from "#/utils/generate-github-auth-url";
import { AllHandsLogoButton } from "#/components/shared/buttons/all-hands-logo-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import OpenHands from "#/api/open-hands";

// Hardcoded translations since we don't want to load i18n
const translations = {
  LOGGING_OUT: "Logging out...",
  LOGGED_OUT: "You have been logged out",
  LOG_IN_WITH_GITHUB: "Log in with GitHub",
  LOGOUT_ERROR: "An error occurred while logging out. Please try again.",
  TRY_AGAIN: "Try Again",
};

export default function LogoutPage() {
  const [isLoggingOut, setIsLoggingOut] = React.useState(true);
  const [hasLogoutError, setHasLogoutError] = React.useState(false);
  const hasAttemptedLogout = React.useRef(false);

  // Generate GitHub auth URL once on mount
  const gitHubAuthUrl = React.useMemo(
    () => generateGitHubAuthUrl("github", new URL(window.location.href)),
    [],
  );

  const performLogout = React.useCallback(async () => {
    // Only attempt logout once
    if (hasAttemptedLogout.current) return;
    hasAttemptedLogout.current = true;

    try {
      // Use the OpenHands API client for consistent headers and error handling
      await OpenHands.logout();

      // Clear any auth-related data from localStorage
      localStorage.removeItem("gh_token");

      setIsLoggingOut(false);
    } catch (error) {
      console.error("Logout error:", error);
      setHasLogoutError(true);
      setIsLoggingOut(false);
    }
  }, []);

  React.useEffect(() => {
    performLogout();
  }, [performLogout]);

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-base">
      <div className="flex flex-col items-center gap-8 p-8 rounded-lg bg-neutral-800">
        <AllHandsLogoButton
          onClick={() => {
            if (gitHubAuthUrl) {
              window.location.href = gitHubAuthUrl;
            }
          }}
        />
        {isLoggingOut ? (
          <div className="flex flex-col items-center gap-4">
            <LoadingSpinner size="large" />
            <span className="text-neutral-200">{translations.LOGGING_OUT}</span>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-neutral-200">
              {hasLogoutError
                ? translations.LOGOUT_ERROR
                : translations.LOGGED_OUT}
            </h1>
            <div className="flex flex-col gap-4">
              {hasLogoutError && (
                <button
                  type="button"
                  onClick={performLogout}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 text-center"
                >
                  {translations.TRY_AGAIN}
                </button>
              )}
              {!hasLogoutError && gitHubAuthUrl && (
                <a
                  href={gitHubAuthUrl}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 text-center"
                >
                  {translations.LOG_IN_WITH_GITHUB}
                </a>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
