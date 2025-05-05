import React from "react";
import { Provider } from "#/types/settings";

interface AuthContextType {
  providerTokensSet: Provider[];
  setProviderTokensSet: (tokens: Provider[]) => void;
  providersAreSet: boolean;
  setProvidersAreSet: (status: boolean) => void;
}

interface AuthContextProps extends React.PropsWithChildren {
  initialProviderTokens?: Provider[];
  initialProvidersAreSet?: boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({
  children,
  initialProviderTokens = [],
  initialProvidersAreSet = false,
}: AuthContextProps) {
  const [providerTokensSet, setProviderTokensSet] = React.useState<Provider[]>(
    initialProviderTokens,
  );

  const [providersAreSet, setProvidersAreSet] = React.useState<boolean>(
    initialProvidersAreSet,
  );

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
