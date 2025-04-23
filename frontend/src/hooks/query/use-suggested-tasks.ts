import { useQuery } from "@tanstack/react-query";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { groupSuggestedTasks } from "#/utils/group-suggested-tasks";
import { useAuth } from "#/context/auth-context";

export const useSuggestedTasks = () => {
  const { providersAreSet } = useAuth();

  return useQuery({
    queryKey: ["tasks"],
    queryFn: SuggestionsService.getSuggestedTasks,
    select: groupSuggestedTasks,
    enabled: providersAreSet,
  });
};
