import React from "react";
import { Branch } from "#/types/git";
import { cn } from "#/utils/utils";
import { BranchItem } from "./branch-item";
import { EmptyState } from "../shared/empty-state";
import { LoadingMoreState } from "../shared/loading-more-state";

export interface BranchDropdownMenuProps {
  isOpen: boolean;
  filteredBranches: Branch[];
  isLoadingState: boolean;
  inputValue: string;
  highlightedIndex: number;
  selectedItem: Branch | null;
  isFetchingNextPage: boolean;
  getMenuProps: any;
  getItemProps: any;
  onScroll: (event: React.UIEvent<HTMLUListElement>) => void;
  menuRef: React.RefObject<HTMLUListElement | null>;
}

export function BranchDropdownMenu({
  isOpen,
  filteredBranches,
  isLoadingState,
  inputValue,
  highlightedIndex,
  selectedItem,
  isFetchingNextPage,
  getMenuProps,
  getItemProps,
  onScroll,
  menuRef,
}: BranchDropdownMenuProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <ul
      {...getMenuProps({
        ref: menuRef,
        onScroll,
        className: cn(
          "absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto",
          isOpen ? "block" : "hidden"
        ),
      })}
      data-testid="git-branch-dropdown-menu"
    >
      {filteredBranches.length === 0 && !isLoadingState ? (
        <li className="px-3 py-2">
          <EmptyState
            inputValue={inputValue}
            searchMessage="No branches found"
            emptyMessage="No branches available"
            testId="git-branch-dropdown-empty"
          />
        </li>
      ) : (
        filteredBranches.map((branch, index) => (
          <BranchItem
            key={branch.name}
            branch={branch}
            isHighlighted={highlightedIndex === index}
            isSelected={selectedItem?.name === branch.name}
            getItemProps={getItemProps}
            index={index}
          />
        ))
      )}
      
      {isFetchingNextPage && (
        <li className="px-3 py-2">
          <LoadingMoreState message="Loading more branches..." />
        </li>
      )}
    </ul>
  );
}