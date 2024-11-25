import posthog from "posthog-js";
import React from "react";
import {
  removeAxiosAuthToken as removeOpenHandsAxiosAuthToken,
  removeAxiosGitHubToken as removeOpenHandsAxiosGitHubToken,
  setAxiosGitHubToken as setOpenHandsAxiosGitHubToken,
  setAxiosAuthToken as setOpenHandsAxiosAuthToken,
} from "#/api/open-hands-axios";
import {
  setAxiosAuthToken as setGitHubAxiosAuthToken,
  removeAxiosAuthToken as removeGitHubAxiosAuthToken,
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

    removeOpenHandsAxiosAuthToken();
  };

  const clearGitHubToken = () => {
    setGitHubTokenState(null);
    localStorage.removeItem("ghToken");

    removeOpenHandsAxiosGitHubToken();
    removeGitHubAxiosAuthToken();
  };

  const setToken = (token: string | null) => {
    setTokenState(token);

    if (token) {
      localStorage.setItem("token", token);
      setOpenHandsAxiosAuthToken(token);
    } else {
      clearToken();
    }
  };

  const setGitHubToken = (token: string | null) => {
    setGitHubTokenState(token);

    if (token) {
      localStorage.setItem("ghToken", token);
      setOpenHandsAxiosGitHubToken(token);
      setGitHubAxiosAuthToken(token);
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
