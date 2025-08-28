import React from "react";
import {
  UseComboboxGetMenuPropsOptions,
  UseComboboxGetItemPropsOptions,
} from "downshift";
import { cn } from "#/utils/utils";

export interface GenericDropdownMenuProps<T> {
  isOpen: boolean;
  filteredItems: T[];
  inputValue: string;
  highlightedIndex: number;
  selectedItem: T | null;
  getMenuProps: <Options>(
    options?: UseComboboxGetMenuPropsOptions & Options,
  ) => any; // eslint-disable-line @typescript-eslint/no-explicit-any
  getItemProps: <Options>(
    options: UseComboboxGetItemPropsOptions<T> & Options,
  ) => any; // eslint-disable-line @typescript-eslint/no-explicit-any
  onScroll?: (event: React.UIEvent<HTMLUListElement>) => void;
  menuRef?: React.RefObject<HTMLUListElement | null>;
  renderItem: (
    item: T,
    index: number,
    highlightedIndex: number,
    selectedItem: T | null,
    getItemProps: <Options>(
      options: UseComboboxGetItemPropsOptions<T> & Options,
    ) => any, // eslint-disable-line @typescript-eslint/no-explicit-any
  ) => React.ReactNode;
  renderEmptyState: (inputValue: string) => React.ReactNode;
}

export function GenericDropdownMenu<T>({
  isOpen,
  filteredItems,
  inputValue,
  highlightedIndex,
  selectedItem,
  getMenuProps,
  getItemProps,
  onScroll,
  menuRef,
  renderItem,
  renderEmptyState,
}: GenericDropdownMenuProps<T>) {
  if (!isOpen) return null;

  return (
    <ul
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...getMenuProps({
        ref: menuRef,
        className: cn(
          "absolute z-10 w-full bg-[#454545] border border-[#717888] rounded-xl shadow-lg max-h-60 overflow-auto",
          "focus:outline-none p-1 gap-2 flex flex-col",
        ),
        onScroll,
      })}
    >
      {filteredItems.length === 0
        ? renderEmptyState(inputValue)
        : filteredItems.map((item, index) =>
            renderItem(
              item,
              index,
              highlightedIndex,
              selectedItem,
              getItemProps,
            ),
          )}
    </ul>
  );
}
