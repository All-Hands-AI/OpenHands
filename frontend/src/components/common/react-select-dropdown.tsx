import { useMemo } from "react";
import Select, { StylesConfig } from "react-select";
import { cn } from "#/utils/utils";

export interface SelectOption {
  value: string;
  label: string;
}

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
  onChange?: (option: SelectOption | null) => void;
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
  onChange,
}: ReactSelectDropdownProps) {
  const customStyles: StylesConfig<SelectOption, false> = useMemo(
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
    }),
    [],
  );

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
