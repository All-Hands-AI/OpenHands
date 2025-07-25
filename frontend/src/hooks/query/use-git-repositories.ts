import { useInfiniteQuery } from "@tanstack/react-query";
import { GitRepository } from "../../types/git";
import { Provider } from "../../types/settings";
import OpenHands from "#/api/open-hands";

interface UseGitRepositoriesOptions {
  provider: Provider;
  pageSize?: number;
  enabled?: boolean;
}

interface GitRepositoriesResponse {
  data: GitRepository[];
  nextPage: number | null;
}

export function useGitRepositories(options: UseGitRepositoriesOptions) {
  const { provider, pageSize = 30, enabled = true } = options;

  return useInfiniteQuery<GitRepositoriesResponse>({
    queryKey: ["git-repositories", provider, pageSize],
    queryFn: async ({ pageParam = 1 }) =>
      OpenHands.retrieveUserGitRepositories(
        provider,
        pageParam as number,
        pageSize,
      ),
    getNextPageParam: (lastPage) => lastPage.nextPage,
    initialPageParam: 1,
    enabled,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
  });
}
