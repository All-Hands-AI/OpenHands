import { useQuery } from "@tanstack/react-query";
import UserService from "#/api/user-service/user-service.api";
import { Provider } from "#/types/settings";

export function useSearchRepositories(
  query: string,
  selectedProvider?: Provider | null,
  disabled?: boolean,
  pageSize: number = 3,
) {
  return useQuery({
    queryKey: ["repositories", "search", query, selectedProvider, pageSize],
    queryFn: () =>
      UserService.searchGitRepositories(
        query,
        pageSize,
        selectedProvider || undefined,
      ),
    enabled: !!query && !!selectedProvider && !disabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
