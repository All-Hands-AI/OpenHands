import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConfig } from "#/hooks/query/use-config";

interface AuthContextType {
  isAuthenticated: boolean;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: React.PropsWithChildren) {
  const queryClient = useQueryClient();
  const { data: config } = useConfig();

  const { data: isAuthenticated, isFetched } = useQuery({
    queryKey: ["authenticate", config?.APP_MODE],
    queryFn: () => OpenHands.authenticate(config!.APP_MODE),
    enabled: !!config?.APP_MODE,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const { mutate: logout } = useMutation({
    mutationFn: OpenHands.logout,
    onSuccess: async () => {
      await queryClient.resetQueries();
    },
  });

  React.useEffect(() => {
    if (isFetched && !isAuthenticated) queryClient.resetQueries();
  }, [isAuthenticated, isFetched]);

  const value = React.useMemo(
    () => ({
      isAuthenticated: isAuthenticated || false,
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
