import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Branch } from "#/types/git";
import { Provider } from "#/types/settings";

export function useSearchBranches(
  repository: string | null,
  query: string,
  perPage: number = 30,
  selectedProvider?: Provider,
) {
  return useQuery<Branch[]>({
    queryKey: [
      "repository",
      repository,
      "branches",
      "search",
      query,
      perPage,
      selectedProvider,
    ],
    queryFn: async () => {
      if (!repository || !query) return [];
      return OpenHands.searchRepositoryBranches(
        repository,
        query,
        perPage,
        selectedProvider,
      );
    },
    enabled: !!repository && !!query,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
  });
}
