import { Autocomplete, AutocompleteItem } from "@heroui/react";
import { ReactNode } from "react";
import { OptionalTag } from "./optional-tag";
import { cn } from "#/utils/utils";

interface SettingsDropdownInputProps {
  testId: string;
  name: string;
  items: { key: React.Key; label: string }[];
  label?: ReactNode;
  wrapperClassName?: string;
  placeholder?: string;
  showOptionalTag?: boolean;
  isDisabled?: boolean;
  defaultSelectedKey?: string;
  isClearable?: boolean;
  onSelectionChange?: (key: React.Key | null) => void;
  onInputChange?: (value: string) => void;
}

export function SettingsDropdownInput({
  testId,
  label,
  wrapperClassName,
  name,
  items,
  placeholder,
  showOptionalTag,
  isDisabled,
  defaultSelectedKey,
  isClearable,
  onSelectionChange,
  onInputChange,
}: SettingsDropdownInputProps) {
  return (
    <label className={cn("flex flex-col gap-2.5", wrapperClassName)}>
      {label && (
        <div className="flex items-center gap-1">
          <span className="text-sm">{label}</span>
          {showOptionalTag && <OptionalTag />}
        </div>
      )}
      <Autocomplete
        aria-label={typeof label === "string" ? label : name}
        data-testid={testId}
        name={name}
        defaultItems={items}
        defaultSelectedKey={defaultSelectedKey}
        onSelectionChange={onSelectionChange}
        onInputChange={onInputChange}
        isClearable={isClearable}
        isDisabled={isDisabled}
        placeholder={placeholder}
        className="w-full"
        classNames={{
          popoverContent: "bg-tertiary rounded-xl border border-[#717888]",
        }}
        inputProps={{
          classNames: {
            inputWrapper:
              "bg-tertiary border border-[#717888] h-10 w-full rounded p-2 placeholder:italic",
          },
        }}
      >
        {(item) => (
          <AutocompleteItem key={item.key}>{item.label}</AutocompleteItem>
        )}
      </Autocomplete>
    </label>
  );
}
