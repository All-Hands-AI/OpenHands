import { useCallback, useMemo } from "react";
import AsyncSelect from "react-select/async";
import { StylesConfig } from "react-select";
import { cn } from "#/utils/utils";

export interface AsyncSelectOption {
  value: string;
  label: string;
}

export interface ReactSelectAsyncDropdownProps {
  loadOptions: (inputValue: string) => Promise<AsyncSelectOption[]>;
  placeholder?: string;
  value?: AsyncSelectOption | null;
  defaultValue?: AsyncSelectOption | null;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isClearable?: boolean;
  cacheOptions?: boolean;
  defaultOptions?: boolean | AsyncSelectOption[];
  onChange?: (option: AsyncSelectOption | null) => void;
  onMenuScrollToBottom?: () => void;
}

export function ReactSelectAsyncDropdown({
  loadOptions,
  placeholder = "Search...",
  value,
  defaultValue,
  className,
  errorMessage,
  disabled = false,
  isClearable = false,
  cacheOptions = true,
  defaultOptions = true,
  onChange,
  onMenuScrollToBottom,
}: ReactSelectAsyncDropdownProps) {
  const customStyles: StylesConfig<AsyncSelectOption, false> = useMemo(
    () => ({
      control: (provided, state) => ({
        ...provided,
        backgroundColor: "#454545", // tertiary
        border: "1px solid #717888",
        borderRadius: "0.125rem",
        minHeight: "2.5rem",
        padding: "0 0.5rem",
        boxShadow: state.isFocused ? "0 0 0 1px #717888" : "none",
        "&:hover": {
          borderColor: "#717888",
        },
      }),
      input: (provided) => ({
        ...provided,
        color: "#ECEDEE", // content
      }),
      placeholder: (provided) => ({
        ...provided,
        fontStyle: "italic",
        color: "#B7BDC2", // tertiary-light
      }),
      singleValue: (provided) => ({
        ...provided,
        color: "#ECEDEE", // content
      }),
      menu: (provided) => ({
        ...provided,
        backgroundColor: "#454545", // tertiary
        border: "1px solid #717888",
        borderRadius: "0.75rem",
      }),
      option: (provided, state) => {
        let backgroundColor = "transparent";
        if (state.isSelected) {
          backgroundColor = "#C9B974"; // primary
        } else if (state.isFocused) {
          backgroundColor = "#24272E"; // base-secondary
        }

        return {
          ...provided,
          backgroundColor,
          color: "#ECEDEE", // content
          "&:hover": {
            backgroundColor: "#24272E", // base-secondary
          },
        };
      },
      clearIndicator: (provided) => ({
        ...provided,
        color: "#B7BDC2", // tertiary-light
        "&:hover": {
          color: "#ECEDEE", // content
        },
      }),
      dropdownIndicator: (provided) => ({
        ...provided,
        color: "#B7BDC2", // tertiary-light
        "&:hover": {
          color: "#ECEDEE", // content
        },
      }),
      loadingIndicator: (provided) => ({
        ...provided,
        color: "#B7BDC2", // tertiary-light
      }),
    }),
    [],
  );

  const handleLoadOptions = useCallback(
    (inputValue: string, callback: (options: AsyncSelectOption[]) => void) => {
      loadOptions(inputValue)
        .then((options) => callback(options))
        .catch(() => callback([]));
    },
    [loadOptions],
  );

  return (
    <div className={cn("w-full", className)}>
      <AsyncSelect
        loadOptions={handleLoadOptions}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        isDisabled={disabled}
        isClearable={isClearable}
        cacheOptions={cacheOptions}
        defaultOptions={defaultOptions}
        onChange={onChange}
        onMenuScrollToBottom={onMenuScrollToBottom}
        styles={customStyles}
        className="w-full"
      />
      {errorMessage && (
        <p className="text-red-500 text-sm mt-1">{errorMessage}</p>
      )}
    </div>
  );
}
