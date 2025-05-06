import { useQuery } from "@tanstack/react-query";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { groupSuggestedTasks } from "#/utils/group-suggested-tasks";

export const useSuggestedTasks = () =>
  useQuery({
    queryKey: ["tasks"],
    queryFn: SuggestionsService.getSuggestedTasks,
    select: groupSuggestedTasks,
  });
