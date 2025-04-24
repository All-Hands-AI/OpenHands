import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

// Instead of directly using useLocation, we'll check the current path manually
// This avoids the Router context requirement
const isOnTosPage = () => {
  // Only run this check in browser environment
  if (typeof window !== "undefined") {
    return window.location.pathname === "/accept-tos";
  }
  return false;
};

export const useConfig = () =>
  useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes,
    enabled: !isOnTosPage(),
  });
