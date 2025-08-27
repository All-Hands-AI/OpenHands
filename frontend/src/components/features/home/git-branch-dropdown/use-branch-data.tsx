import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { Branch, PaginatedBranchesResponse } from "#/types/git";
import { Provider } from "#/types/settings";
import OpenHands from "#/api/open-hands";

export function useBranchData(repository: string | null, provider: Provider) {
  return useInfiniteQuery<PaginatedBranchesResponse, Error>({
    queryKey: ["branches", repository, provider],
    queryFn: async ({ pageParam = 1 }) => {
      if (!repository) {
        throw new Error("Repository is required");
      }
      return OpenHands.getRepositoryBranches(
        repository,
        pageParam as number,
        30,
      );
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.has_next_page ? lastPage.current_page + 1 : undefined,
    enabled: !!repository,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useSearchBranches(
  repository: string | null,
  query: string,
  provider: Provider,
  enabled: boolean = true,
) {
  return useQuery<Branch[], Error>({
    queryKey: ["searchBranches", repository, query, provider],
    queryFn: async () => {
      if (!repository || !query.trim()) {
        return [];
      }
      return OpenHands.searchRepositoryBranches(
        repository,
        query,
        30,
        provider,
      );
    },
    enabled: enabled && !!repository && !!query.trim(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useBranchDataWithDefault(
  repository: string | null,
  provider: Provider,
  defaultBranch: string | null,
  processedSearchInput: string,
  inputValue: string,
  selectedBranch?: Branch | null,
) {
  // Fetch branches with pagination
  const {
    data: branchData,
    fetchNextPage,
    hasNextPage,
    isLoading,
    isFetchingNextPage,
    isError,
  } = useBranchData(repository, provider);

  // Search branches when user types
  const { data: searchData, isLoading: isSearchLoading } = useSearchBranches(
    repository,
    processedSearchInput,
    provider,
    !!processedSearchInput,
  );

  // Search for default branch specifically if it's not in the loaded branches
  const { data: defaultBranchData, isLoading: isDefaultBranchLoading } = useSearchBranches(
    repository,
    defaultBranch || "",
    provider,
    !!defaultBranch && !!repository,
  );

  // Combine all branches from paginated data
  const allBranches = useMemo(
    () => branchData?.pages?.flatMap((page) => page.branches) || [],
    [branchData],
  );

  // Get branches to display with default branch prioritized
  const branches = useMemo(() => {
    // Don't use search results if input exactly matches selected branch
    const shouldUseSearch =
      processedSearchInput &&
      searchData &&
      !(selectedBranch && inputValue === selectedBranch.name);

    let branchesToUse = shouldUseSearch ? searchData : allBranches;

    // If we have a default branch, ensure it's at the top of the list
    if (defaultBranch) {
      // First check if it's already in the current branches
      let defaultBranchObj = branchesToUse.find(branch => branch.name === defaultBranch);
      
      // If not found in current branches, check if we have it from the default branch search
      if (!defaultBranchObj && defaultBranchData && defaultBranchData.length > 0) {
        defaultBranchObj = defaultBranchData.find(branch => branch.name === defaultBranch);
        
        // Add the default branch to the beginning of the list
        if (defaultBranchObj) {
          branchesToUse = [defaultBranchObj, ...branchesToUse];
        }
      } else if (defaultBranchObj) {
        // If found in current branches, move it to the front
        const otherBranches = branchesToUse.filter(branch => branch.name !== defaultBranch);
        branchesToUse = [defaultBranchObj, ...otherBranches];
      }
    }

    return branchesToUse;
  }, [processedSearchInput, searchData, allBranches, selectedBranch, inputValue, defaultBranch, defaultBranchData]);

  return {
    branches,
    allBranches,
    fetchNextPage,
    hasNextPage,
    isLoading: isLoading || isDefaultBranchLoading,
    isFetchingNextPage,
    isError,
    isSearchLoading,
  };
}
