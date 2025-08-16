import Select, {
  StylesConfig,
  GroupBase,
  SelectComponentsConfig,
} from "react-select";
import { useMemo } from "react";
import { cn } from "#/utils/utils";
import { SelectOption, getCustomStyles } from "./react-select-styles";

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
  styles?: StylesConfig<SelectOption, false>;
  components?: SelectComponentsConfig<
    SelectOption,
    false,
    GroupBase<SelectOption>
  >;
  classNamePrefix?: string;
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
  styles,
  components,
  classNamePrefix,
}: ReactSelectDropdownProps) {
  const defaultStyles = useMemo(() => getCustomStyles<SelectOption>(), []);

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
        styles={styles || defaultStyles}
        components={{
          ...components,
        }}
        classNamePrefix={classNamePrefix}
      />
      {errorMessage && (
        <p className="text-red-500 text-sm mt-1">{errorMessage}</p>
      )}
    </div>
  );
}
