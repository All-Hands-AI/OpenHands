import { useMemo } from "react";
import { useRepositoryBranches } from "../../hooks/query/use-repository-branches";
import { ReactSelectDropdown, SelectOption } from "./react-select-dropdown";

export interface GitBranchDropdownProps {
  repositoryName?: string | null;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  testId?: string;
  onChange?: (branchName: string | null) => void;
}

export function GitBranchDropdown({
  repositoryName,
  value,
  placeholder = "Select branch...",
  className,
  errorMessage,
  disabled = false,
  testId,
  onChange,
}: GitBranchDropdownProps) {
  const { data: branches, isLoading } = useRepositoryBranches(
    repositoryName || null,
  );

  const options: SelectOption[] = useMemo(
    () =>
      branches?.map((branch) => ({
        value: branch.name,
        label: branch.name,
      })) || [],
    [branches],
  );

  const hasNoBranches = !isLoading && branches && branches.length === 0;

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value) || null,
    [options, value],
  );

  const handleChange = (option: SelectOption | null) => {
    onChange?.(option?.value || null);
  };

  const isDisabled = disabled || !repositoryName || isLoading || hasNoBranches;

  const displayPlaceholder = hasNoBranches ? "No branches found" : placeholder;
  const displayErrorMessage = hasNoBranches
    ? "This repository has no branches"
    : errorMessage;

  return (
    <ReactSelectDropdown
      testId={testId}
      options={options}
      value={selectedOption}
      placeholder={displayPlaceholder}
      className={className}
      errorMessage={displayErrorMessage}
      disabled={isDisabled}
      isClearable={false}
      isSearchable
      isLoading={isLoading}
      onChange={handleChange}
    />
  );
}
