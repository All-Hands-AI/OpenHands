import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import React from "react";

type AutocompleteItemType = {
  value: string;
  label: string;
};

interface AutocompleteComboboxProps {
  ariaLabel: "model" | "agent";
  items: AutocompleteItemType[];
  defaultKey: string;
}

export const AutocompleteCombobox: React.FC<AutocompleteComboboxProps> = ({
  ariaLabel,
  items,
  defaultKey,
}) => (
  <Autocomplete
    aria-label={ariaLabel}
    defaultItems={items}
    defaultSelectedKey={defaultKey}
  >
    {(item) => (
      <AutocompleteItem key={item.value}>{item.label}</AutocompleteItem>
    )}
  </Autocomplete>
);
