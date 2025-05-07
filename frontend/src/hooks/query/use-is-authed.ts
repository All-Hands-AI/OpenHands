import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";

export const useIsAuthed = () => {
  const { data: config } = useConfig();
  const isOnTosPage = useIsOnTosPage();

  const appMode = config?.APP_MODE;

  return useQuery({
    queryKey: ["user", "authenticated", appMode],
    queryFn: () => OpenHands.authenticate(appMode!),
    enabled: !!appMode && !isOnTosPage,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    retry: false,
    meta: {
      disableToast: true,
    },
  });
};
