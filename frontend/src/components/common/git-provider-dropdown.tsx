import { useMemo } from "react";
import { StylesConfig } from "react-select";
import { Provider } from "../../types/settings";
import { ReactSelectDropdown, SelectOption } from "./react-select-dropdown";

export interface GitProviderDropdownProps {
  providers: Provider[];
  value?: Provider | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isLoading?: boolean;
  onChange?: (provider: Provider | null) => void;
  classNamePrefix?: string;
  styles?: StylesConfig<SelectOption, false>;
}

export function GitProviderDropdown({
  providers,
  value,
  placeholder = "Select Provider",
  className,
  errorMessage,
  disabled = false,
  isLoading = false,
  onChange,
  classNamePrefix,
  styles,
}: GitProviderDropdownProps) {
  const options: SelectOption[] = useMemo(
    () =>
      providers.map((provider) => ({
        value: provider,
        label: provider.charAt(0).toUpperCase() + provider.slice(1),
      })),
    [providers],
  );

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value) || null,
    [options, value],
  );

  const handleChange = (option: SelectOption | null) => {
    onChange?.(option?.value as Provider | null);
  };

  return (
    <ReactSelectDropdown
      options={options}
      value={selectedOption}
      placeholder={placeholder}
      className={className}
      errorMessage={errorMessage}
      disabled={disabled}
      isClearable={false}
      isSearchable={false}
      isLoading={isLoading}
      onChange={handleChange}
      classNamePrefix={classNamePrefix}
      styles={styles}
    />
  );
}
