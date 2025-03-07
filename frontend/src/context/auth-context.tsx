import React from "react";

interface AuthContextType {
  providerTokensSet: Record<string, boolean>;
  setProviderTokensSet: (tokens: Record<string, boolean>) => void;
  providersAreSet: boolean;
  setProvidersAreSet: (status: boolean) => void;
}

interface AuthContextProps extends React.PropsWithChildren {
  initialProviderTokens?: Record<string, boolean>;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({
  children,
  initialProviderTokens = {},
}: AuthContextProps) {
  const [providerTokensSet, setProviderTokensSet] = React.useState<
    Record<string, boolean>
  >(initialProviderTokens);

  const [providersAreSet, setProvidersAreSet] = React.useState<boolean>(false);

  const value = React.useMemo(
    () => ({
      providerTokensSet,
      setProviderTokensSet,
      providersAreSet,
      setProvidersAreSet,
    }),
    [providerTokensSet],
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
