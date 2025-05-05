import { useEffect } from "react";
import { openHands } from "#/api/open-hands-axios";
import { useLogoutHandler } from "#/hooks/useLogoutHandler";

export function AxiosInterceptorSetup() {
  const handleLogoutAndRefresh = useLogoutHandler();

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
