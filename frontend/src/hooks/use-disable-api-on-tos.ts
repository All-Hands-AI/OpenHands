import { useLocation } from "react-router";

/**
 * Custom hook that returns whether API calls should be disabled
 * based on the current route. Used to prevent infinite loops
 * on the TOS page.
 */
export const useDisableApiOnTos = (): boolean => {
  const { pathname } = useLocation();
  return pathname === "/tos";
};
