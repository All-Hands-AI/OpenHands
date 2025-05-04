import { useQuery } from "@tanstack/react-query";
import { getRepositoryBranches } from "#/api/repository-branches";
import { Branch } from "#/types/git";

export const useRepositoryBranches = (repository: string | null) => {
  return useQuery<Branch[]>({
    queryKey: ["repository", repository, "branches"],
    queryFn: async () => {
      if (!repository) return [];
      return getRepositoryBranches(repository);
    },
    enabled: !!repository,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};