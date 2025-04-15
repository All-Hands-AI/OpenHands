import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Provider } from "#/types/settings";

export function useSearchRepositories(
  query: string,
  selectedProvider: Provider | null,
) {
  return useQuery({
    queryKey: ["repositories", query],
    queryFn: () => OpenHands.searchGitRepositories(query, 3),
    enabled: !!query,
    select: (data) => data.map((repo) => ({ ...repo, is_public: true })),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
