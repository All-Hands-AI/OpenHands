import { useQuery, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";

interface UseIsAuthedConfig {
  gitHubToken: string | null;
}

export const useIsAuthed = ({ gitHubToken }: UseIsAuthedConfig) => {
  const queryClient = useQueryClient();
  // Ensure that the app mode is available before fetching user data
  const appMode = queryClient.getQueryData<ReturnType<typeof useConfig>>([
    "config",
  ])?.data?.APP_MODE;

  return useQuery({
    queryKey: ["user", "authenticated", gitHubToken, appMode],
    queryFn: () => OpenHands.authenticate(gitHubToken || "", appMode!),
    enabled: !!appMode,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
