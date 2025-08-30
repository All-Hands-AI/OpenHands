import { useMemo, useEffect } from "react";
import { Provider } from "#/types/settings";
import { GitRepository } from "#/types/git";
import { useGitRepositories } from "#/hooks/query/use-git-repositories";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";

export function useRepositoryData(
  provider: Provider,
  disabled: boolean,
  processedSearchInput: string,
  urlSearchResults: GitRepository[],
  inputValue: string,
  value?: string | null,
) {
  // Fetch user repositories with pagination
  const {
    data: repoData,
    fetchNextPage,
    hasNextPage,
    isLoading,
    isFetchingNextPage,
    isError,
  } = useGitRepositories({
    provider,
    enabled: !disabled,
  });

  // Search repositories when user types
  const { data: searchData, isLoading: isSearchLoading } =
    useSearchRepositories(processedSearchInput, provider);

  // Combine all repositories from paginated data
  const allRepositories = useMemo(
    () => repoData?.pages?.flatMap((page) => page.data) || [],
    [repoData],
  );

  // Find selected repository from all possible sources
  const selectedRepository = useMemo(() => {
    if (!value) return null;

    // Search in all possible repository sources
    const allPossibleRepos = [
      ...allRepositories,
      ...urlSearchResults,
      ...(searchData || []),
    ];

    return allPossibleRepos.find((repo) => repo.id === value) || null;
  }, [allRepositories, urlSearchResults, searchData, value]);

  // Get repositories to display (URL search, regular search, or all repos)
  const repositories = useMemo(() => {
    // Prioritize URL search results when available
    if (urlSearchResults.length > 0) {
      return urlSearchResults;
    }

    // Don't use search results if input exactly matches selected repository
    const shouldUseSearch =
      processedSearchInput &&
      searchData &&
      !(selectedRepository && inputValue === selectedRepository.full_name);

    if (shouldUseSearch) {
      return searchData;
    }
    return allRepositories;
  }, [
    urlSearchResults,
    processedSearchInput,
    searchData,
    allRepositories,
    selectedRepository,
    inputValue,
  ]);

  // Auto-load more repositories when there aren't enough items to create a scrollable dropdown
  // This is particularly important for SaaS mode with installations that might have very few repos
  useEffect(() => {
    const shouldAutoLoad =
      !disabled &&
      !isLoading &&
      !isFetchingNextPage &&
      !isSearchLoading &&
      hasNextPage &&
      !processedSearchInput && // Not during search (use all repos, not search results)
      urlSearchResults.length === 0 &&
      repositories.length > 0 && // Have some repositories loaded
      repositories.length < 10; // But not enough to create a scrollable dropdown

    if (shouldAutoLoad) {
      fetchNextPage();
    }
  }, [
    disabled,
    isLoading,
    isFetchingNextPage,
    isSearchLoading,
    hasNextPage,
    processedSearchInput,
    urlSearchResults.length,
    repositories.length,
    fetchNextPage,
  ]);

  return {
    repositories,
    allRepositories,
    selectedRepository,
    fetchNextPage,
    hasNextPage,
    isLoading,
    isFetchingNextPage,
    isError,
    isSearchLoading,
  };
}
