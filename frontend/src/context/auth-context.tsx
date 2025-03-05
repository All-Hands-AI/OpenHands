import React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConfig } from "#/hooks/query/use-config";

interface AuthContextType {
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: React.PropsWithChildren) {
  const queryClient = useQueryClient();
  const { data: config, isFetched } = useConfig();

  const [isAuthenticated, setIsAuthenticated] = React.useState(false);

  const { mutate: authenticate } = useMutation({
    mutationFn: OpenHands.authenticate,
    onSettled: async (data) => {
      if (!data) {
        setIsAuthenticated(false);
        await queryClient.resetQueries();
      } else {
        setIsAuthenticated(true);
      }
    },
  });

  const { mutate: logout } = useMutation({
    mutationFn: OpenHands.logout,
    onSuccess: async () => {
      setIsAuthenticated(false);
      await queryClient.resetQueries();
    },
  });

  const checkIsAuthed = React.useCallback(() => {
    if (!isFetched) return;
    authenticate(config?.APP_MODE || "saas");
  }, [config?.APP_MODE, isFetched]);

  const value = React.useMemo(
    () => ({
      isAuthenticated,
      logout,
    }),
    [isAuthenticated, logout],
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
