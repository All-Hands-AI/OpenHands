import React from "react";

interface AuthContextType {
  tokenIsSet: boolean;
  setTokenIsSet: (value: boolean) => void;
}

interface AuthContextProps extends React.PropsWithChildren {
  initialTokenIsSet?: boolean;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children, initialTokenIsSet }: AuthContextProps) {
  const [tokenIsSet, setTokenIsSet] = React.useState(
    !!initialTokenIsSet,
  );

  const value = React.useMemo(
    () => ({
      tokenIsSet,
      setTokenIsSet,
    }),
    [tokenIsSet, setTokenIsSet],
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
