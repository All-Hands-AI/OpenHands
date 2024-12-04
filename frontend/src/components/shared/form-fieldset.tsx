import { Autocomplete, AutocompleteItem } from "@nextui-org/react";

interface FormFieldsetProps {
  id: string;
  label: string;
  items: { key: string; value: string }[];
  defaultSelectedKey?: string;
  isClearable?: boolean;
}

export function FormFieldset({
  id,
  label,
  items,
  defaultSelectedKey,
  isClearable,
}: FormFieldsetProps) {
  return (
    <fieldset className="flex flex-col gap-2">
      <label htmlFor={id} className="font-[500] text-[#A3A3A3] text-xs">
        {label}
      </label>
      <Autocomplete
        id={id}
        name={id}
        aria-label={label}
        defaultSelectedKey={defaultSelectedKey}
        isClearable={isClearable}
        inputProps={{
          classNames: {
            inputWrapper: "bg-[#27272A] rounded-md text-sm px-3 py-[10px]",
          },
        }}
      >
        {items.map((item) => (
          <AutocompleteItem key={item.key} value={item.key}>
            {item.value}
          </AutocompleteItem>
        ))}
      </Autocomplete>
    </fieldset>
  );
}
