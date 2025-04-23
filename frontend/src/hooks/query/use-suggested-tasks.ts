import { useQuery } from "@tanstack/react-query";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { groupSuggestedTasks } from "#/utils/group-suggested-tasks";
import { useAuth } from "#/context/auth-context";
import { ProviderOptions } from "#/types/settings";

export const useSuggestedTasks = () => {
  const { providerTokensSet } = useAuth();
  const githubEnabled = providerTokensSet.includes(ProviderOptions.github);

  return useQuery({
    queryKey: ["tasks"],
    queryFn: SuggestionsService.getSuggestedTasks,
    select: groupSuggestedTasks,
    enabled: githubEnabled,
  });
};
