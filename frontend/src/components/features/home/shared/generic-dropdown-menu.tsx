import React from "react";
import { cn } from "#/utils/utils";

export interface GenericDropdownMenuProps<T> {
  isOpen: boolean;
  filteredItems: T[];
  isLoadingState: boolean;
  inputValue: string;
  highlightedIndex: number;
  selectedItem: T | null;
  isFetchingNextPage: boolean;
  getMenuProps: any;
  getItemProps: any;
  onScroll: (event: React.UIEvent<HTMLUListElement>) => void;
  menuRef: React.RefObject<HTMLUListElement | null>;
  renderItem: (item: T, index: number, highlightedIndex: number, selectedItem: T | null, getItemProps: any) => React.ReactNode;
  renderEmptyState: (inputValue: string) => React.ReactNode;
  renderLoadingMoreState: () => React.ReactNode;
}

export function GenericDropdownMenu<T>({
  isOpen,
  filteredItems,
  isLoadingState,
  inputValue,
  highlightedIndex,
  selectedItem,
  isFetchingNextPage,
  getMenuProps,
  getItemProps,
  onScroll,
  menuRef,
  renderItem,
  renderEmptyState,
  renderLoadingMoreState,
}: GenericDropdownMenuProps<T>) {
  if (!isOpen) return null;

  return (
    <ul
      {...getMenuProps({
        ref: menuRef,
        className: cn(
          "absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto",
          "focus:outline-none"
        ),
        onScroll,
      })}
    >
      {isLoadingState ? (
        <li className="px-3 py-2 text-sm text-gray-500">Loading...</li>
      ) : filteredItems.length === 0 ? (
        renderEmptyState(inputValue)
      ) : (
        <>
          {filteredItems.map((item, index) =>
            renderItem(item, index, highlightedIndex, selectedItem, getItemProps)
          )}
          {isFetchingNextPage && renderLoadingMoreState()}
        </>
      )}
    </ul>
  );
}