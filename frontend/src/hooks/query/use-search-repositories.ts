import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export function useSearchRepositories(query: string) {
  return useQuery({
    queryKey: ["repositories", query],
    queryFn: () => OpenHands.searchGitRepositories(query, 3),
    enabled: !!query,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
