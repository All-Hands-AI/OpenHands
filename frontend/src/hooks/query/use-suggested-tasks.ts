import { useQuery } from "@tanstack/react-query";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { groupSuggestedTasks } from "#/utils/group-suggested-tasks";
import { useIsAuthed } from "./use-is-authed";

export const useSuggestedTasks = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["tasks"],
    queryFn: SuggestionsService.getSuggestedTasks,
    select: groupSuggestedTasks,
    enabled: !!userIsAuthenticated,
  });
};
