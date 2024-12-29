import { useQuery } from "@tanstack/react-query";
import { searchPublicRepositories } from "#/api/github";

export function useSearchRepositories(query: string) {
  return useQuery({
    queryKey: ["searchRepositories", query],
    queryFn: () => searchPublicRepositories(query),
    enabled: !!query,
    select: (repos) =>
      repos
        .sort((a, b) => (b.stargazers_count || 0) - (a.stargazers_count || 0))
        .slice(0, 3),
  });
}
