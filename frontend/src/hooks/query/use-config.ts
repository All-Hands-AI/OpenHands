import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router";
import OpenHands from "#/api/open-hands";

export const useConfig = () => {
  const { pathname } = useLocation();
  const isOnTosPage = pathname === "/accept-tos";

  return useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes,
    enabled: !isOnTosPage,
  });
};
