import { useEffect } from "react";
import { openHands } from "#/api/open-hands-axios";
import { useLogoutHandler } from "#/hooks/useLogoutHandler";

interface AxiosInterceptorSetupProps {
  appMode?: string;
}

export function AxiosInterceptorSetup({ appMode }: AxiosInterceptorSetupProps) {
  const handleLogoutAndRefresh = useLogoutHandler(appMode);

  useEffect(() => {
    const interceptor = openHands.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (
          error.response &&
          error.response.status === 401 &&
          localStorage.getItem("providersAreSet") === "true"
        ) {
          await handleLogoutAndRefresh();
        }

        return Promise.reject(error);
      },
    );

    return () => {
      openHands.interceptors.response.eject(interceptor);
    };
  }, [handleLogoutAndRefresh]);

  return null; // It's a logical component
}
