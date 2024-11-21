import posthog from "posthog-js";
import React from "react";

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
  const [token, setToken] = React.useState<string | null>(null);
  const [gitHubToken, setGitHubToken] = React.useState<string | null>(null);

  const clearToken = () => {
    setToken(null);
  };

  const clearGitHubToken = () => {
    setGitHubToken(null);
  };

  const logout = () => {
    clearGitHubToken();
    posthog.reset();
  };

  const value = React.useMemo(
    () => ({
      token,
      gitHubToken,
      setToken,
      setGitHubToken,
      clearToken,
      clearGitHubToken,
      logout,
    }),
    [token, gitHubToken],
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
