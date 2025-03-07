import React from "react";

interface AuthContextType {
  providerTokensSet: Record<string, boolean>;
  setProviderTokensSet: (tokens: Record<string, boolean>) => void;
  githubTokenIsSet: boolean;  // For backward compatibility
  setGitHubTokenIsSet: (value: boolean) => void;  // For backward compatibility
}

interface AuthContextProps extends React.PropsWithChildren {
  initialProviderTokens?: Record<string, boolean>;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children, initialProviderTokens = {} }: AuthContextProps) {
  const [providerTokensSet, setProviderTokensSet] = React.useState<Record<string, boolean>>(
    initialProviderTokens
  );

  const value = React.useMemo(
    () => ({
      providerTokensSet,
      setProviderTokensSet,
      // For backward compatibility, use github token status
      githubTokenIsSet: providerTokensSet.github ?? false,
      setGitHubTokenIsSet: (value: boolean) => 
        setProviderTokensSet(prev => ({ ...prev, github: value })),
    }),
    [providerTokensSet],
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
