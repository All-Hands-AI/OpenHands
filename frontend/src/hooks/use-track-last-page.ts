import { useEffect } from "react";
import { useLocation } from "react-router";
import { useConfig } from "./query/use-config";
import { setLastPage, shouldExcludePath } from "#/utils/local-storage";
import { useIsAuthed } from "./query/use-is-authed";

/**
 * Hook to track the last visited page in local storage
 * Only tracks pages in SAAS mode and excludes certain paths
 */
export const useTrackLastPage = () => {
  const location = useLocation();
  const { data: config } = useConfig();
  const { data: isAuthed, isLoading: isAuthLoading } = useIsAuthed();

  useEffect(() => {
    // Only track pages in SAAS mode when authenticated
    if (config?.APP_MODE !== "saas" || !isAuthed || isAuthLoading) {
      return;
    }

    const { pathname } = location;

    // Don't track excluded paths
    if (shouldExcludePath(pathname)) {
      // leave code block for now as we may decide not to track certain pages.
      // return;
    }

    // Store the current path as the last visited page
    setLastPage(pathname);
  }, [location, config?.APP_MODE]);
};
