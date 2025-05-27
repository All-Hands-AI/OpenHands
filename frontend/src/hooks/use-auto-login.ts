import { useEffect } from "react";
import { useConfig } from "./query/use-config";
import { useIsAuthed } from "./query/use-is-authed";
import { getLoginMethod, LoginMethod } from "#/utils/local-storage";
import { useAuthUrl } from "./use-auth-url";

/**
 * Hook to automatically log in the user if they have a login method stored in local storage
 * Only works in SAAS mode and when the user is not already logged in
 */
export const useAutoLogin = () => {
  const { data: config, isLoading: isConfigLoading } = useConfig();
  const { data: isAuthed, isLoading: isAuthLoading } = useIsAuthed();

  // Get the stored login method
  const loginMethod = getLoginMethod();

  // Get the auth URLs for both providers
  const githubAuthUrl = useAuthUrl({
    appMode: config?.APP_MODE || null,
    identityProvider: "github",
  });

  const gitlabAuthUrl = useAuthUrl({
    appMode: config?.APP_MODE || null,
    identityProvider: "gitlab",
  });

  useEffect(() => {
    // Only auto-login in SAAS mode
    if (config?.APP_MODE !== "saas") {
      return;
    }

    // Wait for auth and config to load
    if (isConfigLoading || isAuthLoading) {
      return;
    }

    // Don't auto-login if already authenticated
    if (isAuthed) {
      return;
    }

    // Don't auto-login if no login method is stored
    if (!loginMethod) {
      return;
    }

    // Get the appropriate auth URL based on the stored login method
    const authUrl =
      loginMethod === LoginMethod.GITHUB ? githubAuthUrl : gitlabAuthUrl;

    // If we have an auth URL, redirect to it
    if (authUrl) {
      // After successful login, the user will be redirected back and can navigate to the last page
      window.location.href = authUrl;
    }
  }, [
    config?.APP_MODE,
    isAuthed,
    isConfigLoading,
    isAuthLoading,
    loginMethod,
    githubAuthUrl,
    gitlabAuthUrl,
  ]);
};
