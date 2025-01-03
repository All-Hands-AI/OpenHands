import { useQuery } from "@tanstack/react-query";
import { searchPublicRepositories } from "#/api/github";

export function useSearchRepositories(query: string) {
  return useQuery({
    queryKey: ["searchRepositories", query],
    queryFn: () => searchPublicRepositories(query, 3),
    enabled: !!query,
    initialData: [],
  });
}
