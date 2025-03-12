import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export function useSearchRepositories(query: string) {
  return useQuery({
    queryKey: ["repositories", query],
    queryFn: () => OpenHands.searchGitHubRepositories(query, 3),
    enabled: !!query,
    select: (data) => data.map((repo) => ({ ...repo, is_public: true })),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
