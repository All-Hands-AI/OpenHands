import { useMemo } from "react";
import { Provider } from "#/types/settings";
import { GitRepository } from "#/types/git";
import { useGitRepositories } from "#/hooks/query/use-git-repositories";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useAppInstallations } from "#/hooks/query/use-app-installations";
import { useConfig } from "#/hooks/query/use-config";
import { shouldUseInstallationRepos } from "#/utils/utils";

export function useRepositoryData(
  provider: Provider,
  disabled: boolean,
  processedSearchInput: string,
  urlSearchResults: GitRepository[],
  inputValue: string,
  value?: string | null,
) {
  const { data: config } = useConfig();
  const useInstallationRepos = shouldUseInstallationRepos(
    provider,
    config?.APP_MODE,
  );

  // Fetch installations first if needed
  const {
    data: installations,
    isSuccess: installationsLoaded,
    isLoading: installationsLoading,
    isError: installationsError,
  } = useAppInstallations(provider);

  // Determine if repositories query should be enabled
  const repositoriesEnabled = useMemo(() => {
    if (disabled) return false;

    // For non-installation repos, enable immediately
    if (!useInstallationRepos) return true;

    // For installation repos, wait until installations are successfully loaded
    return installationsLoaded && installations && installations.length > 0;
  }, [disabled, useInstallationRepos, installationsLoaded, installations]);

  // Fetch user repositories with pagination
  const {
    data: repoData,
    fetchNextPage,
    hasNextPage,
    isLoading: repoLoading,
    isFetchingNextPage,
    isError: repoError,
  } = useGitRepositories({
    provider,
    enabled: repositoriesEnabled,
    installations,
  });

  // Combine loading states
  const isLoading = useInstallationRepos
    ? installationsLoading || repoLoading
    : repoLoading;
  const isError = installationsError || repoError;

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
