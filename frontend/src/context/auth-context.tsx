import React from "react";
import { saveLastPage } from "../utils/last-page";

interface AuthContextType {
  githubTokenIsSet: boolean;
  setGitHubTokenIsSet: (value: boolean) => void;
  logout: () => void;
}

interface AuthContextProps extends React.PropsWithChildren {
  initialGithubTokenIsSet?: boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children, initialGithubTokenIsSet }: AuthContextProps) {
  const [githubTokenIsSet, setGitHubTokenIsSet] = React.useState(
    !!initialGithubTokenIsSet,
  );

  const logout = React.useCallback(() => {
    setGitHubTokenIsSet(false);
    // Save the last page before logging out
    saveLastPage();
    // Clear any auth-related data from localStorage
    localStorage.removeItem("gh_token");
  }, [setGitHubTokenIsSet]);

  const value = React.useMemo(
    () => ({
      githubTokenIsSet,
      setGitHubTokenIsSet,
      logout,
    }),
    [githubTokenIsSet, setGitHubTokenIsSet, logout],
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
