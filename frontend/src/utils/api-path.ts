/**
 * Modifies API paths based on the application mode
 * When APP_MODE is "saas", all calls to "/api/user" are changed to "/api/user/saas"
 *
 * @param path The original API path
 * @param appMode The current application mode ("saas" or "oss")
 * @returns The modified API path
 */
export const getApiPath = (path: string, appMode?: string | null): string => {
  // Only modify paths when APP_MODE is "saas"
  if (appMode === "saas" && path.startsWith("/api/user")) {
    // Check if the path is exactly "/api/user" or has a trailing slash
    if (path === "/api/user" || path === "/api/user/") {
      return "/api/user/saas";
    }

    // For paths like "/api/user/info", "/api/user/repositories", etc.
    return path.replace("/api/user/", "/api/user/saas/");
  }

  return path;
};
