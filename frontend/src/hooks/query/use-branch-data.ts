import { useMemo } from "react";
import { useRepositoryBranchesPaginated } from "./use-repository-branches";
import { useSearchBranches } from "./use-search-branches";
import { Branch } from "#/types/git";
import { Provider } from "#/types/settings";

export function useBranchData(
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
  } = useRepositoryBranchesPaginated(repository);

  // Search branches when user types
  const { data: searchData, isLoading: isSearchLoading } = useSearchBranches(
    repository,
    processedSearchInput,
    30,
    provider,
  );

  // Search for default branch specifically if it's not in the loaded branches
  const { data: defaultBranchData, isLoading: isDefaultBranchLoading } =
    useSearchBranches(repository, defaultBranch || "", 30, provider);

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
      let defaultBranchObj = branchesToUse.find(
        (branch) => branch.name === defaultBranch,
      );

      // If not found in current branches, check if we have it from the default branch search
      if (
        !defaultBranchObj &&
        defaultBranchData &&
        defaultBranchData.length > 0
      ) {
        defaultBranchObj = defaultBranchData.find(
          (branch) => branch.name === defaultBranch,
        );

        // Add the default branch to the beginning of the list
        if (defaultBranchObj) {
          branchesToUse = [defaultBranchObj, ...branchesToUse];
        }
      } else if (defaultBranchObj) {
        // If found in current branches, move it to the front
        const otherBranches = branchesToUse.filter(
          (branch) => branch.name !== defaultBranch,
        );
        branchesToUse = [defaultBranchObj, ...otherBranches];
      }
    }

    return branchesToUse;
  }, [
    processedSearchInput,
    searchData,
    allBranches,
    selectedBranch,
    inputValue,
    defaultBranch,
    defaultBranchData,
  ]);

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
