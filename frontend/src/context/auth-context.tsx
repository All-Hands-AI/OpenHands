import React from "react";

interface AuthContextType {
  githubTokenIsSet: boolean;
  setGitHubTokenIsSet: (value: boolean) => void;
}

interface AuthContextProps extends React.PropsWithChildren {
  initialGithubTokenIsSet?: boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children, initialGithubTokenIsSet }: AuthContextProps) {
  console.log("[AuthProvider] Initializing with initialGithubTokenIsSet:", initialGithubTokenIsSet);
  
  const [githubTokenIsSet, setGitHubTokenIsSet] = React.useState(
    !!initialGithubTokenIsSet,
  );

  // Log when the token state changes
  React.useEffect(() => {
    console.log("[AuthProvider] githubTokenIsSet changed:", githubTokenIsSet);
  }, [githubTokenIsSet]);

  const handleSetGitHubTokenIsSet = React.useCallback((value: boolean) => {
    console.log("[AuthProvider] Setting githubTokenIsSet to:", value);
    setGitHubTokenIsSet(value);
  }, []);

  const value = React.useMemo(
    () => ({
      githubTokenIsSet,
      setGitHubTokenIsSet: handleSetGitHubTokenIsSet,
    }),
    [githubTokenIsSet, handleSetGitHubTokenIsSet],
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
