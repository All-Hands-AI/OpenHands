import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Branch, PaginatedBranchesResponse } from "#/types/git";
import { Provider } from "#/types/settings";
import OpenHands from "#/api/open-hands";

export function useBranchData(repository: string | null, provider: Provider) {
  return useInfiniteQuery<PaginatedBranchesResponse, Error>({
    queryKey: ["branches", repository, provider],
    queryFn: async ({ pageParam = 1 }) => {
      if (!repository) {
        throw new Error("Repository is required");
      }
      return OpenHands.getRepositoryBranches(repository, pageParam as number, 30);
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      return lastPage.has_next_page ? lastPage.current_page + 1 : undefined;
    },
    enabled: !!repository,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useSearchBranches(
  repository: string | null,
  query: string,
  provider: Provider,
  enabled: boolean = true
) {
  return useQuery<Branch[], Error>({
    queryKey: ["searchBranches", repository, query, provider],
    queryFn: async () => {
      if (!repository || !query.trim()) {
        return [];
      }
      return OpenHands.searchRepositoryBranches(repository, query, 30, provider);
    },
    enabled: enabled && !!repository && !!query.trim(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}