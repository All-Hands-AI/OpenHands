import React from "react";

interface AuthContextType {
  providersAreSet: boolean;
  setProvidersAreSet: (status: boolean) => void;
}

interface AuthContextProps extends React.PropsWithChildren {
  initialProvidersAreSet?: boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({
  children,
  initialProvidersAreSet = false,
}: AuthContextProps) {
  const [providersAreSet, setProvidersAreSet] = React.useState<boolean>(
    initialProvidersAreSet,
  );

  const value = React.useMemo(
    () => ({
      providersAreSet,
      setProvidersAreSet,
    }),
    [providersAreSet, setProvidersAreSet],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export { AuthProvider };
