import posthog from "posthog-js";
import React from "react";
import OpenHands from "#/api/open-hands";
import {
  removeGitHubTokenHeader as removeOpenHandsGitHubTokenHeader,
  setGitHubTokenHeader as setOpenHandsGitHubTokenHeader,
  setupOpenhandsAxiosInterceptors
} from "#/api/open-hands-axios";
import {
  setAuthTokenHeader as setGitHubAuthTokenHeader,
  removeAuthTokenHeader as removeGitHubAuthTokenHeader,
  setupAxiosInterceptors as setupGithubAxiosInterceptors,
} from "#/api/github-axios-instance";

interface AuthContextType {
  gitHubToken: string | null;
  keycloakToken: string | null;
  setUserId: (userId: string) => void;
  setAccessTokens: (gitHubToken: string | null, keycloakToken: string | null) => void;
  clearAccessTokens: () => void;
  refreshToken: () => Promise<boolean>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: React.PropsWithChildren) {
  const [gitHubTokenState, setGitHubTokenState] = React.useState<string | null>(
    () => localStorage.getItem("ghToken"),
  );

  const [keycloakTokenState, setKeycloakTokenState] = React.useState<string | null>(
    () => localStorage.getItem("kcToken"),
  );

  const [userIdState, setUserIdState] = React.useState<string>(
    () => localStorage.getItem("userId") || "",
  );

  const clearAccessTokens = () => {
    console.log("clearAccessTokens")
    setGitHubTokenState(null);
    setKeycloakTokenState(null);
    setUserIdState("");
    localStorage.removeItem("ghToken");
    localStorage.removeItem("kcToken");
    localStorage.removeItem("userId");

    removeOpenHandsGitHubTokenHeader();
    removeGitHubAuthTokenHeader();
  };

  const setAccessTokens = (gitHubToken: string | null, keycloakToken: string | null) => {
    console.log(`setAccessTokens keycloakToken: ${keycloakToken}`)
    setGitHubTokenState(gitHubToken);
    setKeycloakTokenState(keycloakToken);

    if (gitHubToken && keycloakToken) {
      localStorage.setItem("ghToken", gitHubToken);
      localStorage.setItem("kcToken", keycloakToken);
      setOpenHandsGitHubTokenHeader(keycloakToken);
      setGitHubAuthTokenHeader(gitHubToken);
    } else {
      clearAccessTokens();
    }
  };

  const setUserId = (userId: string) => {
    console.log(`setUserId userId: ${userId}`)
    setUserIdState(userId);
    localStorage.setItem("userId", userId);
  };

  const logout = () => {
    clearAccessTokens();
    posthog.reset();
  };

  const refreshToken = async (): Promise<boolean> => {
    // const config = await OpenHands.getConfig();

    // if (config.APP_MODE !== "saas" || !gitHubTokenState) {
    //   return false;
    // }

    const stored_userid = localStorage.getItem("userId") || ""
    const data = await OpenHands.refreshToken("saas", stored_userid);
    if (data) {
      setAccessTokens(data.providerAccessToken, data.keycloakAccessToken);
      return true;
    }

    clearAccessTokens();
    return false;
  };

  React.useEffect(() => {
    const storedGitHubToken = localStorage.getItem("ghToken");
    const storedKeycloakToken = localStorage.getItem("kcToken");

    const userId = localStorage.getItem("userId") || "";

    setAccessTokens(storedGitHubToken, storedKeycloakToken);
    setUserId(userId);
    setupGithubAxiosInterceptors(refreshToken, logout);
    setupOpenhandsAxiosInterceptors(refreshToken, logout)
  }, []);

  const value = React.useMemo(
    () => ({
      gitHubToken: gitHubTokenState,
      keycloakToken: keycloakTokenState,
      setAccessTokens,
      setUserId,
      clearAccessTokens,
      refreshToken,
      logout,
    }),
    [gitHubTokenState, keycloakTokenState],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within a AuthProvider");
  }
  return context;
}

export { AuthProvider, useAuth };
