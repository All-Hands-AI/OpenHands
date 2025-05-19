import { useEffect } from "react";
import { useLocation } from "react-router";
import { useConfig } from "./query/use-config";
import { setLastPage, shouldExcludePath } from "#/utils/local-storage";

/**
 * Hook to track the last visited page in local storage
 * Only tracks pages in SAAS mode and excludes settings pages and root app URL
 */
export const useTrackLastPage = () => {
  const location = useLocation();
  const { data: config } = useConfig();

  useEffect(() => {
    // Only track pages in SAAS mode
    if (config?.APP_MODE !== "saas") {
      return;
    }

    const { pathname } = location;

    // Don't track excluded paths
    if (shouldExcludePath(pathname)) {
      return;
    }

    // Store the current path as the last visited page
    setLastPage(pathname);
  }, [location, config?.APP_MODE]);
};
