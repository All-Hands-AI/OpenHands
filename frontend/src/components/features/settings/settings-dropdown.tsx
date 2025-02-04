import React from "react";
import { OptionalTag } from "./optional-tag";
import { cn } from "#/utils/utils";

interface SettingsDropdownProps {
  testId?: string;
  name?: string;
  label: string;
  options: { label: string; value: string }[];
  onOptionSelect?: (value: string) => void;
  defaultValue?: string;
  isDisabled?: boolean;
  showOptionalTag?: boolean;
  className?: string;
}

export function SettingsDropdown({
  testId,
  name,
  label,
  options,
  onOptionSelect,
  defaultValue,
  isDisabled,
  showOptionalTag,
  className,
}: SettingsDropdownProps) {
  const defaultLabel = options.find(
    (option) => option.value === defaultValue,
  )?.label;

  const [dropdownIsOpen, setDropdownIsOpen] = React.useState(false);
  const [selectedOption, setSelectedOption] = React.useState("");
  const [dropdownOptions, setDropdownOptions] = React.useState(options);

  const handleInputChange = (value: string) => {
    const filteredOptions = options.filter((option) =>
      option.label.toLowerCase().includes(value.toLowerCase()),
    );
    setSelectedOption(value);
    setDropdownOptions(filteredOptions);
  };

  const handleSelectOption = (option: { label: string; value: string }) => {
    onOptionSelect?.(option.value);
    setSelectedOption(option.label);
    setDropdownIsOpen(false);
    setDropdownOptions(options);
  };

  return (
    <div className="relative w-fit">
      <label
        onFocus={() => setDropdownIsOpen(true)}
        onBlur={() => setDropdownIsOpen(false)}
        className={cn("flex flex-col gap-2.5 w-full", className)}
      >
        <div className="flex items-center gap-1">
          <span className="text-sm">{label}</span>
          {showOptionalTag && <OptionalTag />}
        </div>
        <input
          data-testid={testId}
          name={name}
          disabled={isDisabled}
          type="text"
          className={cn(
            "bg-[#454545] border border-[#717888] h-10 w-full rounded p-2",
            "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
          )}
          value={selectedOption || defaultLabel}
          onChange={(e) => handleInputChange(e.target.value)}
        />
      </label>

      {dropdownIsOpen && (
        <div
          data-testid="dropdown"
          className="absolute bg-[#454545] border border-[#717888] top-[calc(100%+0.25rem)] w-full rounded-xl max-h-60 overflow-y-auto z-10"
        >
          {dropdownOptions.map((option) => (
            <div
              key={option.value}
              data-testid="dropdown-option"
              className="p-2 cursor-pointer hover:bg-[#717888] first:rounded-t-xl last:rounded-b-xl"
              onMouseDown={() => handleSelectOption(option)}
            >
              {option.label}
            </div>
          ))}
          {dropdownOptions.length === 0 && (
            <div data-testid="no-options" className="p-2 italic">
              No options found
            </div>
          )}
        </div>
      )}
    </div>
  );
}
