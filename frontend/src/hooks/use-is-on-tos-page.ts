import { useLocation } from "react-router";

/**
 * Hook to check if the current page is the Terms of Service acceptance page.
 *
 * @returns {boolean} True if the current page is the TOS acceptance page, false otherwise.
 */
export const useIsOnTosPage = (): boolean => {
  const { pathname } = useLocation();
  return pathname === "/accept-tos";
};
