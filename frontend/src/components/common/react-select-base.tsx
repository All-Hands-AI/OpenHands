import { useCallback, useMemo } from "react";
import Select from "react-select";
import AsyncSelect from "react-select/async";
import { cn } from "#/utils/utils";
import { SelectOptionBase, getCustomStyles } from "./react-select-styles";

export type SelectOption = SelectOptionBase;

export interface ReactSelectBaseProps {
  placeholder?: string;
  value?: SelectOption | null;
  defaultValue?: SelectOption | null;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isClearable?: boolean;
  isLoading?: boolean;
  onChange?: (option: SelectOption | null) => void;
  testId?: string;
}

export interface ReactSelectSyncProps extends ReactSelectBaseProps {
  options: SelectOption[];
  isSearchable?: boolean;
}

export interface ReactSelectAsyncProps extends ReactSelectBaseProps {
  loadOptions: (inputValue: string) => Promise<SelectOption[]>;
  cacheOptions?: boolean;
  defaultOptions?: boolean | SelectOption[];
  onMenuScrollToBottom?: () => void;
}

export type ReactSelectProps = 
  | (ReactSelectSyncProps & { type: "sync" })
  | (ReactSelectAsyncProps & { type: "async" });

export function ReactSelect({
  type,
  placeholder = type === "sync" ? "Select option..." : "Search...",
  value,
  defaultValue,
  className,
  errorMessage,
  disabled = false,
  isClearable = false,
  isLoading = false,
  onChange,
  testId,
  ...props
}: ReactSelectProps) {
  const customStyles = useMemo(() => getCustomStyles<SelectOption>(), []);

  const handleLoadOptions = useCallback(
    (inputValue: string, callback: (options: SelectOption[]) => void) => {
      if (type === "async") {
        props.loadOptions(inputValue)
          .then((options) => callback(options))
          .catch(() => callback([]));
      }
    },
    [type, props.loadOptions],
  );

  const SelectComponent = type === "sync" ? Select : AsyncSelect;
  const selectProps = type === "sync" 
    ? {
        options: props.options,
        isSearchable: props.isSearchable ?? true,
      }
    : {
        loadOptions: handleLoadOptions,
        cacheOptions: props.cacheOptions ?? true,
        defaultOptions: props.defaultOptions ?? true,
        onMenuScrollToBottom: props.onMenuScrollToBottom,
      };

  return (
    <div data-testid={testId} className={cn("w-full", className)}>
      <SelectComponent
        {...selectProps}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        isDisabled={disabled}
        isClearable={isClearable}
        isLoading={isLoading}
        onChange={onChange}
        styles={customStyles}
        className="w-full"
      />
      {errorMessage && (
        <p
          data-testid={testId ? `${testId}-error` : undefined}
          className="text-red-500 text-sm mt-1"
        >
          {errorMessage}
        </p>
      )}
    </div>
  );
}