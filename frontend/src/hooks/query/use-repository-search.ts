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

  // Combine and sort repositories
  const repositories = [
    ...(userRepos.data?.pages.flatMap((page) => page.data) ?? []),
    ...(searchResults.data?.data ?? []),
  ];

  // Remove duplicates based on full_name, preferring public repos with stars
  const uniqueRepositories = repositories.filter(
    (repo, index, self) =>
      index === self.findIndex((r) => r.full_name === repo.full_name)
  );

  // Sort repositories: prefix matches first, then by stars, then alphabetically
  const sortedRepositories = uniqueRepositories.sort((a, b) => {
    const query = debouncedQuery.toLowerCase();
    const aIsPrefix = a.full_name.toLowerCase().startsWith(query);
    const bIsPrefix = b.full_name.toLowerCase().startsWith(query);

    // If one is a prefix match and the other isn't, prefer the prefix match
    if (aIsPrefix !== bIsPrefix) {
      return aIsPrefix ? -1 : 1;
    }

    // If both or neither are prefix matches, sort by stars
    if (a.stargazers_count !== b.stargazers_count) {
      return b.stargazers_count - a.stargazers_count;
    }

    // If stars are equal, sort alphabetically
    return a.full_name.localeCompare(b.full_name);
  });

  return {
    repositories: sortedRepositories,
    isLoading: userRepos.isLoading || searchResults.isLoading,
    error: userRepos.error || searchResults.error,
  };
};