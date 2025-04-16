import { useMemo } from "react";

/**
 * Custom hook that returns whether API calls should be disabled
 * based on the current URL. Used to prevent infinite loops
 * on the TOS page.
 *
 * This hook doesn't use useLocation to avoid Router context requirements,
 * making it safe to use in components outside Router context.
 */
export const useDisableApiOnTos = (): boolean =>
  // Memoize the result to prevent unnecessary re-renders
  useMemo(() => {
    // Get the current URL path from window.location
    const currentPath = window.location.pathname;
    const currentUrl = window.location.href;

    // Check if the current path is the TOS page
    const isTosPage = currentPath === "/tos";

    // Also check if we're on an external TOS page that might be redirected
    const isExternalTosPage =
      currentPath.includes("/tos") || currentUrl.includes("all-hands.dev/tos");

    return isTosPage || isExternalTosPage;
  }, []);
