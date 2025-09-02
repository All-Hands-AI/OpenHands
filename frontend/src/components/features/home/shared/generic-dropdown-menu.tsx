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
  stickyFooterItem?: React.ReactNode;
  testId?: string;
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
  stickyFooterItem,
  testId,
}: GenericDropdownMenuProps<T>) {
  if (!isOpen) return null;

  const hasItems = filteredItems.length > 0;
  const showEmptyState = !hasItems && !stickyFooterItem;

  return (
    <div className="relative">
      <ul
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...getMenuProps({
          ref: menuRef,
          className: cn(
            "absolute z-10 w-full bg-[#454545] border border-[#727987] rounded-lg shadow-none",
            "focus:outline-none mt-1 z-[9999] max-h-60 overflow-auto",
            stickyFooterItem ? "pb-0" : "p-1",
          ),
          onScroll,
          "data-testid": testId,
        })}
      >
        {showEmptyState
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
        {stickyFooterItem && (
          <li className="sticky bottom-0 border-t border-[#727987] bg-[#454545] p-1 -mb-1">
            {stickyFooterItem}
          </li>
        )}
      </ul>
    </div>
  );
}
