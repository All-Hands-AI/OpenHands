import { useQuery } from "@tanstack/react-query";
import { searchPublicRepositories } from "#/api/github";

export function useSearchRepositories(query: string) {
  return useQuery({
    queryKey: ["repositories", query],
    queryFn: () => searchPublicRepositories(query, 3),
    enabled: !!query,
    select: (data) => data.map((repo) => ({ ...repo, is_public: true })),
    initialData: [],
  });
}
