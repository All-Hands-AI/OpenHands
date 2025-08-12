import { GroupBase, SelectComponentsConfig, StylesConfig } from "react-select";
import { useCallback, useMemo } from "react";
import AsyncSelect from "react-select/async";
import { cn } from "#/utils/utils";
import {
  SelectOption,
  SelectOptionBase,
  getCustomStyles,
} from "./react-select-styles";

export type AsyncSelectOption = SelectOptionBase;

export interface ReactSelectAsyncDropdownProps {
  loadOptions: (inputValue: string) => Promise<AsyncSelectOption[]>;
  testId?: string;
  placeholder?: string;
  value?: AsyncSelectOption | null;
  defaultValue?: AsyncSelectOption | null;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isClearable?: boolean;
  isLoading?: boolean;
  cacheOptions?: boolean;
  defaultOptions?: boolean | AsyncSelectOption[];
  onChange?: (option: AsyncSelectOption | null) => void;
  onMenuScrollToBottom?: () => void;
  styles?: StylesConfig<SelectOption, false>;
  classNamePrefix?: string;
  components?: SelectComponentsConfig<
    SelectOption,
    false,
    GroupBase<SelectOption>
  >;
}

export function ReactSelectAsyncDropdown({
  loadOptions,
  testId,
  placeholder = "Search...",
  value,
  defaultValue,
  className,
  errorMessage,
  disabled = false,
  isClearable = false,
  isLoading = false,
  cacheOptions = true,
  defaultOptions = true,
  onChange,
  onMenuScrollToBottom,
  styles,
  classNamePrefix,
  components,
}: ReactSelectAsyncDropdownProps) {
  const customStyles = useMemo(() => getCustomStyles<AsyncSelectOption>(), []);

  const handleLoadOptions = useCallback(
    (inputValue: string, callback: (options: AsyncSelectOption[]) => void) => {
      loadOptions(inputValue)
        .then((options) => callback(options))
        .catch(() => callback([]));
    },
    [loadOptions],
  );

  return (
    <div data-testid={testId} className={cn("w-full", className)}>
      <AsyncSelect
        loadOptions={handleLoadOptions}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        isDisabled={disabled}
        isClearable={isClearable}
        isLoading={isLoading}
        cacheOptions={cacheOptions}
        defaultOptions={defaultOptions}
        onChange={onChange}
        onMenuScrollToBottom={onMenuScrollToBottom}
        styles={styles || customStyles}
        className="w-full"
        components={{
          ...components,
        }}
        classNamePrefix={classNamePrefix}
      />
      {errorMessage && (
        <p
          data-testid="repo-dropdown-error"
          className="text-red-500 text-sm mt-1"
        >
          {errorMessage}
        </p>
      )}
    </div>
  );
}
