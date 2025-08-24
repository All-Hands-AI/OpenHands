import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Branch } from "#/types/git";

export const useRepositoryBranches = (repository: string | null) =>
  useQuery<Branch[]>({
    queryKey: ["repository", repository, "branches"],
    queryFn: async () => {
      if (!repository) return [];
      return OpenHands.getRepositoryBranches(repository);
    },
    enabled: !!repository,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

export const useRepositoryBranchesPaginated = (
  repository: string | null,
  perPage: number = 30,
) =>
  useInfiniteQuery<Branch[], Error>({
    queryKey: ["repository", repository, "branches", "paginated", perPage],
    queryFn: async ({ pageParam = 1 }) => {
      if (!repository) return [];
      return OpenHands.getRepositoryBranches(
        repository,
        pageParam as number,
        perPage,
      );
    },
    enabled: !!repository,
    staleTime: 1000 * 60 * 5, // 5 minutes
    getNextPageParam: (lastPage, allPages) => {
      // If the last page has fewer items than perPage, we've reached the end
      if (lastPage.length < perPage) return undefined;
      return allPages.length + 1;
    },
    initialPageParam: 1,
  });
