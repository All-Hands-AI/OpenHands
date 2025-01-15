import posthog from "posthog-js";
import React from "react";
import OpenHands from "#/api/open-hands";
import { setupAxiosInterceptors as setupGithubAxiosInterceptors } from "#/api/github-axios-instance";

interface AuthContextType {
  setUserId: (userId: string) => void;
  refreshToken: () => Promise<boolean>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: React.PropsWithChildren) {
  const [userIdState, setUserIdState] = React.useState<string>(
    () => localStorage.getItem("userId") || "",
  );

  const setUserId = (userId: string) => {
    setUserIdState(userIdState);
    localStorage.setItem("userId", userId);
  };

  const logout = () => {
    posthog.reset();
  };

  const refreshToken = async (): Promise<boolean> => {
    const config = await OpenHands.getConfig();

    if (config.APP_MODE !== "saas") {
      return false;
    }

    const newToken = await OpenHands.refreshToken(config.APP_MODE, userIdState);
    if (newToken) {
      return true;
    }

    return false;
  };

  React.useEffect(() => {
    const userId = localStorage.getItem("userId") || "";

    setUserId(userId);
    const setupIntercepter = async () => {
      const config = await OpenHands.getConfig();
      setupGithubAxiosInterceptors(config.APP_MODE, refreshToken, logout);
    };

    setupIntercepter();
  }, []);

  const value = React.useMemo(
    () => ({
      setUserId,
      refreshToken,
      logout,
    }),
    [setUserId, refreshToken, logout],
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
