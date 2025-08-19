import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Branch } from "#/types/git";

export const useRepositoryBranches = (repository: string | null) =>
  useQuery<Branch[]>({
    queryKey: ["repository", repository, "branches"],
    queryFn: async () => {
      if (!repository) return [];
      try {
        return await OpenHands.getRepositoryBranches(repository);
      } catch {
        // If we can't list branches (e.g., missing/invalid token), treat as no branches
        return [];
      }
    },
    enabled: !!repository,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
