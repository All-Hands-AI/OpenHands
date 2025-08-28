import React from "react";
import { cn } from "#/utils/utils";

interface DropdownItemProps<T> {
  item: T;
  index: number;
  isHighlighted: boolean;
  isSelected: boolean;
  getItemProps: <Options>(options: any & Options) => any; // eslint-disable-line @typescript-eslint/no-explicit-any
  getDisplayText: (item: T) => string;
  getItemKey: (item: T) => string;
}

export function DropdownItem<T>({
  item,
  index,
  isHighlighted,
  isSelected,
  getItemProps,
  getDisplayText,
  getItemKey,
}: DropdownItemProps<T>) {
  const itemProps = getItemProps({
    index,
    item,
    className: cn(
      "px-3 py-2 cursor-pointer text-sm rounded-lg mx-0.5 my-0.5",
      "text-[#ECEDEE] focus:outline-none",
      {
        "bg-[#24272E]": isHighlighted && !isSelected,
        "bg-[#C9B974] text-black": isSelected,
        "hover:bg-[#24272E]": !isSelected,
        "hover:bg-[#C9B974] hover:text-black": isSelected,
      },
    ),
  });

  return (
    // eslint-disable-next-line react/jsx-props-no-spreading
    <li key={getItemKey(item)} {...itemProps}>
      <span className="font-medium">{getDisplayText(item)}</span>
    </li>
  );
}
