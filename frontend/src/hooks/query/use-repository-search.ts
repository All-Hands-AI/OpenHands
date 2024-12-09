import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { retrieveGitHubUserRepositories, searchGitHubRepositories } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import debounce from "lodash/debounce";

export const useRepositorySearch = (searchQuery: string) => {
  const { gitHubToken } = useAuth();
  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);

  useEffect(() => {
    const handler = debounce((query: string) => {
      setDebouncedQuery(query);
    }, 300);

    handler(searchQuery);
    return () => handler.cancel();
  }, [searchQuery]);

  const userRepos = useInfiniteQuery({
    queryKey: ["repositories", gitHubToken],
    queryFn: async ({ pageParam }) =>
      retrieveGitHubUserRepositories(pageParam, 100),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: !!gitHubToken,
  });

  const searchResults = useQuery({
    queryKey: ["repository-search", debouncedQuery],
    queryFn: () => searchGitHubRepositories(debouncedQuery),
    enabled: !!debouncedQuery,
  });

  // Combine user repos and search results
  const repositories = [
    ...(userRepos.data?.pages.flatMap((page) => page.data) ?? []),
    ...(searchResults.data?.data ?? []),
  ];

  // Remove duplicates based on full_name
  const uniqueRepositories = repositories.filter(
    (repo, index, self) =>
      index === self.findIndex((r) => r.full_name === repo.full_name)
  );

  return {
    repositories: uniqueRepositories,
    isLoading: userRepos.isLoading || searchResults.isLoading,
    error: userRepos.error || searchResults.error,
  };
};