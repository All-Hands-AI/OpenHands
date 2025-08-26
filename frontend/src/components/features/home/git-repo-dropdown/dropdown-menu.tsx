import React from "react";
import { cn } from "#/utils/utils";
import { GitRepository } from "#/types/git";
import { RepositoryItem } from "./repository-item";
import { EmptyState } from "./empty-state";
import { LoadingMoreState } from "./loading-more-state";

interface DropdownMenuProps {
  isOpen: boolean;
  filteredRepositories: GitRepository[];
  isLoadingState: boolean;
  inputValue: string;
  highlightedIndex: number;
  selectedItem: GitRepository | null;
  isFetchingNextPage: boolean;
  getMenuProps: any;
  getItemProps: any;
  onScroll: (event: React.UIEvent<HTMLUListElement>) => void;
  menuRef: React.RefObject<HTMLUListElement | null>;
}

export function DropdownMenu({
  isOpen,
  filteredRepositories,
  isLoadingState,
  inputValue,
  highlightedIndex,
  selectedItem,
  isFetchingNextPage,
  getMenuProps,
  getItemProps,
  onScroll,
  menuRef,
}: DropdownMenuProps) {
  return (
    <ul
      {...getMenuProps({
        ref: menuRef,
        onScroll,
        className: cn(
          "absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg",
          "max-h-60 overflow-auto",
          !isOpen && "hidden"
        ),
      })}
      data-testid="git-repo-dropdown-menu"
    >
      {isOpen && (
        <>
          {filteredRepositories.length === 0 && !isLoadingState && (
            <EmptyState inputValue={inputValue} />
          )}
          
          {filteredRepositories.map((repository, index) => (
            <RepositoryItem
              key={repository.id}
              repository={repository}
              index={index}
              highlightedIndex={highlightedIndex}
              selectedItem={selectedItem}
              getItemProps={getItemProps}
            />
          ))}
          
          {isFetchingNextPage && <LoadingMoreState />}
        </>
      )}
    </ul>
  );
}