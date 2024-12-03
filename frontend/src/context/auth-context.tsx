import posthog from "posthog-js";
import React from "react";
import {
  removeAuthTokenHeader as removeOpenHandsAuthTokenHeader,
  removeGitHubTokenHeader as removeOpenHandsGitHubTokenHeader,
  setGitHubTokenHeader as setOpenHandsGitHubTokenHeader,
  setAuthTokenHeader as setOpenHandsAuthTokenHeader,
} from "#/api/open-hands-axios";
import {
  setAuthTokenHeader as setGitHubAuthTokenHeader,
  removeAuthTokenHeader as removeGitHubAuthTokenHeader,
} from "#/api/github-axios-instance";

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

  const clearToken = () => {
    setTokenState(null);
    localStorage.removeItem("token");

    removeOpenHandsAuthTokenHeader();
  };

  const clearGitHubToken = () => {
    setGitHubTokenState(null);
    localStorage.removeItem("ghToken");

    removeOpenHandsGitHubTokenHeader();
    removeGitHubAuthTokenHeader();
  };

  const setToken = (token: string | null) => {
    setTokenState(token);

    if (token) {
      localStorage.setItem("token", token);
      setOpenHandsAuthTokenHeader(token);
    } else {
      clearToken();
    }
  };

  const setGitHubToken = (token: string | null) => {
    setGitHubTokenState(token);

    if (token) {
      localStorage.setItem("ghToken", token);
      setOpenHandsGitHubTokenHeader(token);
      setGitHubAuthTokenHeader(token);
    } else {
      clearGitHubToken();
    }
  };

  React.useEffect(() => {
    const storedToken = localStorage.getItem("token");
    const storedGitHubToken = localStorage.getItem("ghToken");

    setToken(storedToken);
    setGitHubToken(storedGitHubToken);
  }, []);

  const logout = () => {
    clearGitHubToken();
    posthog.reset();
  };

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
