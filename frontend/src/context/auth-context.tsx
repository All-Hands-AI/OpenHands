import posthog from "posthog-js";
import React from "react";
import OpenHands from "#/api/open-hands";

interface AuthContextType {
  token: string | null;
  gitHubToken: string | null;
  setToken: (token: string | null) => void;
  setGitHubToken: (token: string | null) => void;
  clearToken: () => void;
  clearGitHubToken: () => void;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: React.PropsWithChildren) {
  const [tokenState, setTokenState] = React.useState<string | null>(() =>
    localStorage.getItem("token"),
  );
  const [gitHubTokenState, setGitHubTokenState] = React.useState<string | null>(
    () => localStorage.getItem("ghToken"),
  );

  const [gitHubTokenTime, setGitHubTokenTime] = React.useState<string | null>(
    () => localStorage.getItem("ghTokenTime"),
  );

  React.useLayoutEffect(() => {
    setTokenState(localStorage.getItem("token"));
    setGitHubTokenState(localStorage.getItem("ghToken"));
  });

  const setToken = (token: string | null) => {
    setTokenState(token);

    if (token) localStorage.setItem("token", token);
    else localStorage.removeItem("token");
  };

  const setGitHubToken = (token: string | null) => {
    setGitHubTokenState(token);

    if (token) {
      localStorage.setItem("ghToken", token);
      const timestamp = new Date().toISOString();
      localStorage.setItem("ghTokenTime", timestamp);
      setGitHubTokenTime(timestamp);
    } else {
      localStorage.removeItem("ghToken");
      localStorage.removeItem("ghTokenTime");
    }
  };

  const clearToken = () => {
    setTokenState(null);
    localStorage.removeItem("token");
  };

  const clearGitHubToken = () => {
    setGitHubTokenState(null);
    localStorage.removeItem("ghToken");
    localStorage.removeItem("ghTokenTime");
  };

  const logout = () => {
    clearGitHubToken();
    posthog.reset();
  };

  const refreshToken = async () => {
    const config = await OpenHands.getConfig();

    if (config.APP_MODE !== "saas" || !gitHubTokenState) {
      return;
    }

    let needsRefresh = false;

    if (!gitHubTokenTime) {
      // Refresh if the timestamp is missing
      needsRefresh = true;
    } else {
      // Refresh if more than 7 hours old
      const timeDiff = Date.now() - new Date(gitHubTokenTime).getTime();
      needsRefresh = timeDiff > 7 * 60 * 60 * 1000;
    }

    if (!needsRefresh) {
      return;
    }

    const newToken = await OpenHands.refreshToken(
      gitHubTokenState,
      config.APP_MODE,
    );
    if (newToken) {
      setGitHubToken(newToken);
    } else {
      clearGitHubToken();
    }
  };
  React.useEffect(() => {
    refreshToken();
  }, [gitHubTokenState, gitHubTokenTime]);

  const value = React.useMemo(
    () => ({
      token: tokenState,
      gitHubToken: gitHubTokenState,
      setToken,
      setGitHubToken,
      clearToken,
      clearGitHubToken,
      logout,
    }),
    [tokenState, gitHubTokenState],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within a AuthProvider");
  }
  return context;
}

export { AuthProvider, useAuth };
