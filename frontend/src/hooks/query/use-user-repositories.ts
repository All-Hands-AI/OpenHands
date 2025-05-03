import { useQuery } from "@tanstack/react-query";
import { useAuth } from "#/context/auth-context";
import OpenHands from "#/api/open-hands";

export const useUserRepositories = () => {
  const { providerTokensSet, providersAreSet } = useAuth();

  return useQuery({
    queryKey: ["repositories", providerTokensSet],
    queryFn: OpenHands.retrieveUserGitRepositories,
    enabled: providersAreSet,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
