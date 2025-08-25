import { useMemo, useState, useEffect } from "react";
import { useRepositoryBranchesPaginated } from "../../hooks/query/use-repository-branches";
import { useSearchBranches } from "../../hooks/query/use-search-branches";
import { useDebounce } from "../../hooks/use-debounce";
import { InfiniteScrollSelect, SelectOption } from "./infinite-scroll-select";

export interface GitBranchDropdownProps {
  repositoryName?: string | null;
  defaultBranch?: string | null;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  onChange?: (branchName: string | null) => void;
}

export function GitBranchDropdown({
  repositoryName,
  defaultBranch,
  value,
  placeholder = "Select branch...",
  className,
  errorMessage,
  disabled = false,
  onChange,
}: GitBranchDropdownProps) {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const { data, isLoading, hasNextPage, fetchNextPage, isFetchingNextPage } =
    useRepositoryBranchesPaginated(repositoryName || null);
  const { data: searchResults, isLoading: isSearchLoading } = useSearchBranches(
    repositoryName || null,
    debouncedSearch,
    30,
  );

  const options: SelectOption[] = useMemo(() => {
    if (debouncedSearch && searchResults) {
      return searchResults.map((b) => ({ value: b.name, label: b.name }));
    }
    if (!data?.pages) return [];
    
    const allBranches = data.pages.flatMap((page) => page.branches);
    const branchOptions = allBranches.map((branch) => ({
      value: branch.name,
      label: branch.name,
    }));
    
    // When not searching, prioritize the default branch by moving it to the front
    if (defaultBranch && !debouncedSearch) {
      const defaultBranchIndex = branchOptions.findIndex(
        (option) => option.value === defaultBranch
      );
      if (defaultBranchIndex > 0) {
        const defaultBranchOption = branchOptions[defaultBranchIndex];
        branchOptions.splice(defaultBranchIndex, 1);
        branchOptions.unshift(defaultBranchOption);
      }
    }
    
    return branchOptions;
  }, [data, debouncedSearch, searchResults, defaultBranch]);

  const hasNoBranches =
    !isLoading &&
    data?.pages &&
    data.pages.every((page) => page.branches.length === 0);

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value) || null,
    [options, value],
  );

  // Auto-select default branch when no branch is selected and no search is active
  useEffect(() => {
    if (
      defaultBranch &&
      !value &&
      !debouncedSearch &&
      options.length > 0 &&
      options.some((option) => option.value === defaultBranch)
    ) {
      onChange?.(defaultBranch);
    }
  }, [defaultBranch, value, debouncedSearch, options, onChange]);

  const handleChange = (option: SelectOption | null) => {
    onChange?.(option?.value || null);
  };

  const handleLoadMore = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  const isDisabled =
    disabled ||
    !repositoryName ||
    (isLoading && !debouncedSearch) ||
    hasNoBranches;

  const displayPlaceholder = hasNoBranches ? "No branches found" : placeholder;
  const displayErrorMessage = hasNoBranches
    ? "This repository has no branches"
    : errorMessage;

  return (
    <InfiniteScrollSelect
      options={options}
      value={selectedOption}
      placeholder={displayPlaceholder}
      className={className}
      errorMessage={displayErrorMessage}
      disabled={isDisabled}
      isClearable={false}
      isSearchable
      isLoading={isLoading || isSearchLoading}
      hasNextPage={debouncedSearch ? false : hasNextPage}
      onLoadMore={handleLoadMore}
      onChange={handleChange}
      onInputChange={(val) => setSearch(val)}
    />
  );
}
