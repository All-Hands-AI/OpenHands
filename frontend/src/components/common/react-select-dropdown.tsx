import { useMemo } from "react";
import Select, { StylesConfig } from "react-select";
import { cn } from "#/utils/utils";
import { SelectOptionBase, getCustomStyles } from "./react-select-styles";

export type SelectOption = SelectOptionBase;

export interface ReactSelectDropdownProps {
  options: SelectOption[];
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
  classNamePrefix?: string;
  styles?: StylesConfig<SelectOption, false>;
}

export function ReactSelectDropdown({
  options,
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
  classNamePrefix,
  styles,
}: ReactSelectDropdownProps) {
  const customStyles = useMemo(() => getCustomStyles<SelectOption>(), []);

  return (
    <div className={cn("w-full", className)}>
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
        styles={styles || customStyles}
        className="w-full"
        classNamePrefix={classNamePrefix}
      />
      {errorMessage && (
        <p className="text-red-500 text-sm mt-1">{errorMessage}</p>
      )}
    </div>
  );
}
