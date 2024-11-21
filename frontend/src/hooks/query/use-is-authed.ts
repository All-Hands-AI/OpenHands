import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";

interface UseIsAuthedConfig {
  gitHubToken: string | null;
}

export const useIsAuthed = ({ gitHubToken }: UseIsAuthedConfig) => {
  const { data: config } = useConfig();

  return useQuery({
    queryKey: ["user", "authenticated", gitHubToken, config],
    queryFn: () => OpenHands.authenticate(gitHubToken || "", config!.APP_MODE),
    enabled: !!config?.APP_MODE,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
