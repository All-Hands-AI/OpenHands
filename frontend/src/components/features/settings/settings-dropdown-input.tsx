import { Autocomplete, AutocompleteItem } from "@heroui/react";
import { ReactNode } from "react";
import { OptionalTag } from "./optional-tag";

interface SettingsDropdownInputProps {
  testId: string;
  label: ReactNode;
  name: string;
  items: { key: React.Key; label: string }[];
  showOptionalTag?: boolean;
  isDisabled?: boolean;
  defaultSelectedKey?: string;
  isClearable?: boolean;
}

export function SettingsDropdownInput({
  testId,
  label,
  name,
  items,
  showOptionalTag,
  isDisabled,
  defaultSelectedKey,
  isClearable,
}: SettingsDropdownInputProps) {
  return (
    <label className="flex flex-col gap-2 w-full">
      <div className="flex items-center gap-1">
        <span className="text-[14px] font-medium text-[#595B57]">{label}</span>
        {showOptionalTag && <OptionalTag />}
      </div>
      <Autocomplete
        aria-label={typeof label === "string" ? label : name}
        data-testid={testId}
        name={name}
        defaultItems={items}
        defaultSelectedKey={defaultSelectedKey}
        isClearable={isClearable}
        isDisabled={isDisabled}
        className="w-full"
        classNames={{
          popoverContent:
            "bg-[#1E1E1F] rounded-xl border border-[#232521] text-[14px] font-medium text-[#EFEFEF]",
        }}
        inputProps={{
          classNames: {
            inputWrapper:
              "bg-[#1E1E1F] border border-[#232521] h-11 w-full rounded-lg p-2 placeholder:italic",
            input: "text-[14px] font-medium text-[#EFEFEF]",
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
