import { useLocation } from "react-router";
import { useMemo } from "react";

/**
 * Custom hook that returns whether API calls should be disabled
 * based on the current route. Used to prevent infinite loops
 * on the TOS page.
 */
export const useDisableApiOnTos = (): boolean => {
  const { pathname } = useLocation();

  // Memoize the result to prevent unnecessary re-renders
  return useMemo(() => {
    // Check if the current path is the TOS page
    const isTosPage = pathname === "/tos";

    // Also check if we're on an external TOS page that might be redirected
    const isExternalTosPage =
      pathname.includes("/tos") ||
      window.location.href.includes("all-hands.dev/tos");

    return isTosPage || isExternalTosPage;
  }, [pathname]);
};
