import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import React from "react";

type AutocompleteItemType = {
  value: string;
  label: string;
};

interface AutocompleteComboboxProps {
  ariaLabel: "model" | "agent" | "language";
  items: AutocompleteItemType[];
  defaultKey: string;
  onChange: (key: string) => void;
}

export const AutocompleteCombobox: React.FC<AutocompleteComboboxProps> = ({
  ariaLabel,
  items,
  defaultKey,
  onChange,
}) => (
  <Autocomplete
    aria-label={ariaLabel}
    defaultItems={items}
    defaultSelectedKey={defaultKey}
    onSelectionChange={(key) => {
      if (typeof key === "string") onChange(key);
    }}
  >
    {(item) => (
      <AutocompleteItem key={item.value}>{item.label}</AutocompleteItem>
    )}
  </Autocomplete>
);
