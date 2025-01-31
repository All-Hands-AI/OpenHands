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

  return (
    <div>
      <label
        onFocus={() => setDropdownIsOpen(true)}
        onBlur={() => setDropdownIsOpen(false)}
        className={cn("flex flex-col gap-2.5 w-fit", className)}
      >
        <div className="flex items-center gap-1">
          <span className="text-sm">{label}</span>
          {showOptionalTag && <OptionalTag />}
        </div>
        <input
          data-testid={testId}
          type="text"
          value={selectedOption}
          onChange={(e) => {
            const filteredOptions = options.filter((option) =>
              option.label.toLowerCase().includes(e.target.value.toLowerCase()),
            );
            setSelectedOption(e.target.value);
            setDropdownOptions(filteredOptions);
          }}
          className="bg-[#454545] border border-[#717888] h-10 w-full rounded p-2"
        />
      </label>

      {dropdownIsOpen && (
        <div data-testid="dropdown">
          {dropdownOptions.map((option) => (
            <div
              key={option.value}
              data-testid="dropdown-option"
              onMouseDown={() => {
                setSelectedOption(option.label);
                setDropdownIsOpen(false);
                setDropdownOptions(options);
              }}
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
