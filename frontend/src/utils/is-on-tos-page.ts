/**
 * Checks if the current page is the Terms of Service acceptance page.
 * This function works outside of React Router context by checking window.location directly.
 *
 * @param {string} [pathname] - Optional pathname from React Router's useLocation hook
 * @returns {boolean} True if the current page is the TOS acceptance page, false otherwise.
 */
export const isOnTosPage = (pathname?: string): boolean => {
  // If pathname is provided (from React Router), use it
  if (pathname !== undefined) {
    return pathname === "/accept-tos";
  }

  // Otherwise check window.location (works outside React Router context)
  if (typeof window !== "undefined") {
    return window.location.pathname === "/accept-tos";
  }

  return false;
};
