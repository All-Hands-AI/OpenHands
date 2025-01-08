import posthog from "posthog-js";
import React from "react";
import OpenHands from "#/api/open-hands";
import {
  removeGitHubTokenHeader,
  setGitHubTokenHeader,
} from "#/api/open-hands-axios";

interface AuthContextType {
  gitHubToken: string | null;
  setUserId: (userId: string) => void;
  setGitHubToken: (token: string | null) => void;
  clearGitHubToken: () => void;
  refreshToken: () => Promise<boolean>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: React.PropsWithChildren) {
  const [gitHubTokenState, setGitHubTokenState] = React.useState<string | null>(
    () => localStorage.getItem("ghToken"),
  );

  const [userIdState, setUserIdState] = React.useState<string>(
    () => localStorage.getItem("userId") || "",
  );

  const clearGitHubToken = () => {
    setGitHubTokenState(null);
    setUserIdState("");
    localStorage.removeItem("ghToken");
    localStorage.removeItem("userId");

    removeGitHubTokenHeader();
  };

  const setGitHubToken = (token: string | null) => {
    setGitHubTokenState(token);

    if (token) {
      localStorage.setItem("ghToken", token);
      setGitHubTokenHeader(token);
    } else {
      clearGitHubToken();
    }
  };

  const setUserId = (userId: string) => {
    setUserIdState(userIdState);
    localStorage.setItem("userId", userId);
  };

  const logout = () => {
    clearGitHubToken();
    posthog.reset();
  };

  const refreshToken = async (): Promise<boolean> => {
    const config = await OpenHands.getConfig();

    if (config.APP_MODE !== "saas" || !gitHubTokenState) {
      return false;
    }

    const newToken = await OpenHands.refreshToken(config.APP_MODE, userIdState);
    if (newToken) {
      setGitHubToken(newToken);
      return true;
    }

    clearGitHubToken();
    return false;
  };

  React.useEffect(() => {
    const storedGitHubToken = localStorage.getItem("ghToken");

    const userId = localStorage.getItem("userId") || "";

    setGitHubToken(storedGitHubToken);
    setUserId(userId);
  }, []);

  const value = React.useMemo(
    () => ({
      gitHubToken: gitHubTokenState,
      setGitHubToken,
      setUserId,
      clearGitHubToken,
      refreshToken,
      logout,
    }),
    [gitHubTokenState],
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
