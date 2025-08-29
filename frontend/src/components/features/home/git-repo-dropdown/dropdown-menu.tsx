import React from "react";
import {
  UseComboboxGetMenuPropsOptions,
  UseComboboxGetItemPropsOptions,
} from "downshift";
import { GitRepository } from "#/types/git";
import { DropdownItem } from "../shared/dropdown-item";
import { GenericDropdownMenu, EmptyState } from "../shared";

interface DropdownMenuProps {
  isOpen: boolean;
  filteredRepositories: GitRepository[];
  inputValue: string;
  highlightedIndex: number;
  selectedItem: GitRepository | null;
  getMenuProps: <Options>(
    options?: UseComboboxGetMenuPropsOptions & Options,
  ) => any; // eslint-disable-line @typescript-eslint/no-explicit-any
  getItemProps: <Options>(
    options: UseComboboxGetItemPropsOptions<GitRepository> & Options,
  ) => any; // eslint-disable-line @typescript-eslint/no-explicit-any
  onScroll: (event: React.UIEvent<HTMLUListElement>) => void;
  menuRef: React.RefObject<HTMLUListElement | null>;
}

export function DropdownMenu({
  isOpen,
  filteredRepositories,
  inputValue,
  highlightedIndex,
  selectedItem,
  getMenuProps,
  getItemProps,
  onScroll,
  menuRef,
}: DropdownMenuProps) {
  const renderItem = (
    repository: GitRepository,
    index: number,
    currentHighlightedIndex: number,
    currentSelectedItem: GitRepository | null,
    currentGetItemProps: <Options>(
      options: UseComboboxGetItemPropsOptions<GitRepository> & Options,
    ) => any, // eslint-disable-line @typescript-eslint/no-explicit-any
  ) => (
    <DropdownItem
      key={repository.id}
      item={repository}
      index={index}
      isHighlighted={currentHighlightedIndex === index}
      isSelected={currentSelectedItem?.id === repository.id}
      getItemProps={currentGetItemProps}
      getDisplayText={(repo) => repo.full_name}
      getItemKey={(repo) => repo.id.toString()}
    />
  );

  const renderEmptyState = (currentInputValue: string) => (
    <EmptyState inputValue={currentInputValue} />
  );

  return (
    <div data-testid="git-repo-dropdown-menu">
      <GenericDropdownMenu
        isOpen={isOpen}
        filteredItems={filteredRepositories}
        inputValue={inputValue}
        highlightedIndex={highlightedIndex}
        selectedItem={selectedItem}
        getMenuProps={getMenuProps}
        getItemProps={getItemProps}
        onScroll={onScroll}
        menuRef={menuRef}
        renderItem={renderItem}
        renderEmptyState={renderEmptyState}
      />
    </div>
  );
}
