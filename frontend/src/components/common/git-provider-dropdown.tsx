import { StylesConfig } from "react-select";
import { useMemo } from "react";
import { Provider } from "../../types/settings";
import { ReactSelectDropdown } from "./react-select-dropdown";
import { GitProviderIcon } from "../shared/git-provider-icon";
import { SelectOption } from "./react-select-styles";
import { ReactSelectCustomControl } from "./react-select-custom-control";

export interface GitProviderDropdownProps {
  providers: Provider[];
  value?: Provider | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isLoading?: boolean;
  onChange?: (provider: Provider | null) => void;
  styles?: StylesConfig<SelectOption, false>;
  classNamePrefix?: string;
}

/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable react/jsx-props-no-spreading */
export function GitProviderDropdown({
  providers,
  value,
  placeholder = "Select Provider",
  className,
  errorMessage,
  disabled = false,
  isLoading = false,
  onChange,
  styles,
  classNamePrefix,
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
      styles={styles}
      components={{
        IndicatorSeparator: () => null,
        Control: (props) => (
          <ReactSelectCustomControl
            {...props}
            startIcon={
              selectedOption && (
                <GitProviderIcon
                  gitProvider={selectedOption.value as Provider}
                  className="min-w-[14px] min-h-[14px] w-[14px] h-[14px]"
                />
              )
            }
          />
        ),
      }}
      classNamePrefix={classNamePrefix}
    />
  );
}
