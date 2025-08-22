import { StylesConfig } from "react-select";
import { useMemo } from "react";
import { useRepositoryBranches } from "../../hooks/query/use-repository-branches";
import { ReactSelectDropdown } from "./react-select-dropdown";
import BranchIcon from "#/icons/u-code-branch.svg?react";
import { SelectOption } from "./react-select-styles";
import { ReactSelectCustomControl } from "./react-select-custom-control";

export interface GitBranchDropdownProps {
  repositoryName?: string | null;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  testId?: string;
  onChange?: (branchName: string | null) => void;
  styles?: StylesConfig<SelectOption, false>;
  classNamePrefix?: string;
}

/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable react/jsx-props-no-spreading */
export function GitBranchDropdown({
  repositoryName,
  value,
  placeholder = "Select branch...",
  className,
  errorMessage,
  disabled = false,
  testId,
  onChange,
  styles,
  classNamePrefix,
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
      components={{
        IndicatorSeparator: () => null,
        Control: (props) => (
          <ReactSelectCustomControl
            {...props}
            startIcon={<BranchIcon width={16} height={16} />}
          />
        ),
      }}
      styles={styles}
      classNamePrefix={classNamePrefix}
    />
  );
}
