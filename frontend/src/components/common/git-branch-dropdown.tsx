import { useMemo, useState } from "react";
import { useRepositoryBranchesPaginated } from "../../hooks/query/use-repository-branches";
import { useSearchBranches } from "../../hooks/query/use-search-branches";
import { InfiniteScrollSelect, SelectOption } from "./infinite-scroll-select";

export interface GitBranchDropdownProps {
  repositoryName?: string | null;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  onChange?: (branchName: string | null) => void;
}

export function GitBranchDropdown({
  repositoryName,
  value,
  placeholder = "Select branch...",
  className,
  errorMessage,
  disabled = false,
  onChange,
}: GitBranchDropdownProps) {
  const [search, setSearch] = useState("");
  const { data, isLoading, hasNextPage, fetchNextPage, isFetchingNextPage } =
    useRepositoryBranchesPaginated(repositoryName || null);
  const { data: searchResults, isLoading: isSearchLoading } = useSearchBranches(
    repositoryName || null,
    search,
    30,
  );

  const options: SelectOption[] = useMemo(() => {
    if (search && searchResults) {
      return searchResults.map((b) => ({ value: b.name, label: b.name }));
    }
    if (!data?.pages) return [];
    return data.pages.flatMap((page) =>
      page.branches.map((branch) => ({
        value: branch.name,
        label: branch.name,
      })),
    );
  }, [data, search, searchResults]);

  const hasNoBranches =
    !isLoading &&
    data?.pages &&
    data.pages.every((page) => page.branches.length === 0);

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value) || null,
    [options, value],
  );

  const handleChange = (option: SelectOption | null) => {
    onChange?.(option?.value || null);
  };

  const handleLoadMore = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  const isDisabled =
    disabled || !repositoryName || (isLoading && !search) || hasNoBranches;

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
      hasNextPage={hasNextPage}
      onLoadMore={handleLoadMore}
      onChange={handleChange}
      onInputChange={setSearch}
    />
  );
}
