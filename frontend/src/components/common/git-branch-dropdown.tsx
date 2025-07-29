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

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value) || null,
    [options, value],
  );

  const handleChange = (option: SelectOption | null) => {
    onChange?.(option?.value || null);
  };

  const isDisabled = disabled || !repositoryName || isLoading;

  return (
    <ReactSelectDropdown
      options={options}
      value={selectedOption}
      placeholder={placeholder}
      className={className}
      errorMessage={errorMessage}
      disabled={isDisabled}
      isClearable={false}
      isSearchable
      isLoading={isLoading}
      onChange={handleChange}
    />
  );
}
