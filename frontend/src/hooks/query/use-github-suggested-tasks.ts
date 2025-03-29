import { useQuery } from "@tanstack/react-query";
import { retrieveGitHubSuggestedTasks, SuggestedTask } from "#/api/github";

export const useGitHubSuggestedTasks = () =>
  useQuery<SuggestedTask[], Error>({
    queryKey: ["github", "suggested-tasks"],
    queryFn: retrieveGitHubSuggestedTasks,
    retry: false,
  });
