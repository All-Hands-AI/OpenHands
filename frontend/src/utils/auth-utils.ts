/**
 * Utility functions for authentication
 */

/**
 * Creates a logout handler function
 * @param appMode The current app mode
 * @returns A function that handles logout and browser refresh
 */
export const createLogoutHandler =
  (appMode: string | undefined) => async (): Promise<void> => {
    if (appMode === "saas") {
      try {
        const baseURL = `${window.location.protocol}//${
          import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host
        }`;
        await fetch(`${baseURL}/api/logout`, {
          method: "POST",
          credentials: "include",
        });
      } catch (error) {
        // Error during logout is not critical as we'll refresh anyway
      } finally {
        window.location.reload();
      }
    }
  };
