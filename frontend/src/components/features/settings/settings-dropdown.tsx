import React from "react";
import { OptionalTag } from "./optional-tag";
import { cn } from "#/utils/utils";

interface SettingsDropdownProps {
  testId?: string;
  label: string;
  options: { label: string; value: string }[];
  showOptionalTag?: boolean;
  className?: string;
}

export function SettingsDropdown({
  testId,
  label,
  options,
  showOptionalTag,
  className,
}: SettingsDropdownProps) {
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
          type="text"
          className="bg-[#454545] border border-[#717888] h-10 w-full rounded p-2"
          value={selectedOption}
          onChange={(e) => handleInputChange(e.target.value)}
        />
      </label>

      {dropdownIsOpen && (
        <div
          data-testid="dropdown"
          className="absolute bg-[#454545] border border-[#717888] border-t-0 w-full rounded-b-xl"
        >
          {dropdownOptions.map((option) => (
            <div
              key={option.value}
              data-testid="dropdown-option"
              className="p-2 cursor-pointer hover:bg-[#717888] last:rounded-b-xl"
              onMouseDown={() => handleSelectOption(option)}
            >
              {option.label}
            </div>
          ))}
          {dropdownOptions.length === 0 && (
            <div data-testid="no-options">No options found</div>
          )}
        </div>
      )}
    </div>
  );
}
