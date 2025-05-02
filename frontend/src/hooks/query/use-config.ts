import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";

// We need to fetch the config regardless of authentication state
// as it's needed to determine the app mode and other essential settings
export const useConfig = () => {
  const isOnTosPage = useIsOnTosPage();

  return useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes,
    enabled: !isOnTosPage,
  });
};
