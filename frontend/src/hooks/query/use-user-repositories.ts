import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Provider } from "#/types/settings";

export const useUserRepositories = (provider: Provider | null) =>
  useQuery({
    queryKey: ["repositories"],
    queryFn: OpenHands.retrieveUserGitRepositories,
    enabled: !!provider,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
