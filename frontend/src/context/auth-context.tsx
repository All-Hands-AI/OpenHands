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
  const [githubTokenIsSet, setGitHubTokenIsSet] = React.useState(
    !!initialGithubTokenIsSet,
  );

  const value = React.useMemo(
    () => ({
      githubTokenIsSet,
      setGitHubTokenIsSet,
    }),
    [githubTokenIsSet, setGitHubTokenIsSet],
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
