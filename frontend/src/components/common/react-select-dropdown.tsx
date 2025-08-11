import { useMemo } from "react";
import Select from "react-select";
import { cn } from "#/utils/utils";
import { SelectOptionBase, getCustomStyles } from "./react-select-styles";

export type SelectOption = SelectOptionBase;

export interface ReactSelectDropdownProps {
  options: SelectOption[];
  testId?: string;
  placeholder?: string;
  value?: SelectOption | null;
  defaultValue?: SelectOption | null;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isClearable?: boolean;
  isSearchable?: boolean;
  isLoading?: boolean;
  onChange?: (option: SelectOption | null) => void;
}

export function ReactSelectDropdown({
  options,
  testId,
  placeholder = "Select option...",
  value,
  defaultValue,
  className,
  errorMessage,
  disabled = false,
  isClearable = false,
  isSearchable = true,
  isLoading = false,
  onChange,
}: ReactSelectDropdownProps) {
  const customStyles = useMemo(() => getCustomStyles<SelectOption>(), []);

  return (
    <div data-testid={testId} className={cn("w-full", className)}>
      <Select
        options={options}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        isDisabled={disabled}
        isClearable={isClearable}
        isSearchable={isSearchable}
        isLoading={isLoading}
        onChange={onChange}
        styles={customStyles}
        className="w-full"
      />
      {errorMessage && (
        <p className="text-red-500 text-sm mt-1">{errorMessage}</p>
      )}
    </div>
  );
}
