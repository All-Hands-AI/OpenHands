/**
 * Utility functions for authentication
 */

/**
 * Handles logout and browser refresh
 * @param appMode The current app mode
 */
export const handleLogoutAndRefresh = async (
  appMode: string,
): Promise<void> => {
  try {
    // Construct the endpoint based on app mode
    const endpoint =
      appMode === "saas" ? "/api/logout" : "/api/unset-provider-tokens";

    // Make a direct axios call to the logout endpoint
    const baseURL = `${window.location.protocol}//${import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host}`;
    await fetch(`${baseURL}${endpoint}`, {
      method: "POST",
      credentials: "include",
    });
  } catch (error) {
    console.error("Error during logout:", error);
  } finally {
    // Always refresh the browser
    window.location.reload();
  }
};
