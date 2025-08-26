import React, { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { useCombobox } from "downshift";
import { Branch } from "#/types/git";
import { Provider } from "#/types/settings";
import { cn } from "#/utils/utils";
import { useBranchData, useSearchBranches } from "./use-branch-data";
import { LoadingSpinner } from "../shared/loading-spinner";
import { ClearButton } from "../shared/clear-button";
import { ToggleButton } from "../shared/toggle-button";
import { ErrorMessage } from "../shared/error-message";
import { BranchDropdownMenu } from "./branch-dropdown-menu";

export interface GitBranchDropdownProps {
  repository: string | null;
  provider: Provider;
  selectedBranch: Branch | null;
  onBranchSelect: (branch: Branch | null) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function GitBranchDropdown({
  repository,
  provider,
  selectedBranch,
  onBranchSelect,
  placeholder = "Select branch...",
  disabled = false,
  className,
}: GitBranchDropdownProps) {
  const [inputValue, setInputValue] = useState("");
  const [isUserSearching, setIsUserSearching] = useState(false);
  const menuRef = useRef<HTMLUListElement>(null);

  // Use branch data hooks
  const {
    data: branchPages,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useBranchData(repository, provider);

  const {
    data: searchResults,
    isLoading: isSearchLoading,
  } = useSearchBranches(repository, inputValue, provider);

  // Flatten paginated results
  const allBranches = useMemo(() => {
    if (!branchPages?.pages) return [];
    return branchPages.pages.flatMap(page => page.branches || []);
  }, [branchPages]);

  // Determine which branches to display
  const filteredBranches = useMemo(() => {
    // Only show search results if user is actively searching (not just displaying selected value)
    if (isUserSearching && inputValue.trim() && searchResults) {
      return searchResults || [];
    }
    return allBranches;
  }, [isUserSearching, inputValue, searchResults, allBranches]);

  // Handle clear
  const handleClear = useCallback(() => {
    setInputValue("");
    setIsUserSearching(false);
    onBranchSelect(null);
  }, [onBranchSelect]);

  // Handle branch selection
  const handleBranchSelect = useCallback((branch: Branch | null) => {
    onBranchSelect(branch);
    setInputValue("");
    setIsUserSearching(false);
  }, [onBranchSelect]);

  // Handle input value change
  const handleInputValueChange = useCallback(({ inputValue: newInputValue }: { inputValue?: string }) => {
    if (newInputValue !== undefined) {
      setInputValue(newInputValue);
      // Mark as user searching if they're typing something different from selected branch
      setIsUserSearching(true);
    }
  }, []);

  // Handle menu scroll for infinite loading
  const handleMenuScroll = useCallback((event: React.UIEvent<HTMLUListElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
    if (scrollHeight - scrollTop <= clientHeight * 1.5 && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Downshift configuration
  const {
    isOpen,
    selectedItem,
    highlightedIndex,
    getInputProps,
    getItemProps,
    getMenuProps,
    getToggleButtonProps,
  } = useCombobox({
    items: filteredBranches,
    selectedItem: selectedBranch,
    itemToString: (item) => item?.name || "",
    onSelectedItemChange: ({ selectedItem: newSelectedItem }) => {
      handleBranchSelect(newSelectedItem || null);
    },
    onInputValueChange: handleInputValueChange,
    onIsOpenChange: ({ isOpen: newIsOpen }) => {
      // When dropdown opens, reset search state so all branches are shown
      if (newIsOpen && !isUserSearching) {
        setIsUserSearching(false);
      }
    },
    inputValue,
  });

  // Initialize input value when selectedBranch changes (but not when user is typing)
  useEffect(() => {
    if (selectedBranch && !isOpen && inputValue !== selectedBranch.name) {
      setInputValue(selectedBranch.name);
      setIsUserSearching(false); // Not searching when displaying selected value
    } else if (!selectedBranch && !isOpen && inputValue) {
      setInputValue("");
      setIsUserSearching(false);
    }
  }, [selectedBranch, isOpen, inputValue]);

  const isLoadingState = isLoading || isSearchLoading || isFetchingNextPage;

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <input
          {...getInputProps({
            disabled: disabled || !repository,
            placeholder,
            className: cn(
              "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "disabled:bg-gray-100 disabled:cursor-not-allowed",
              "pr-10" // Space for toggle button
            ),
          })}
          data-testid="git-branch-dropdown-input"
        />
        
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
          {selectedBranch && (
            <ClearButton disabled={disabled} onClear={handleClear} />
          )}
          
          <ToggleButton 
            isOpen={isOpen} 
            disabled={disabled || !repository} 
            getToggleButtonProps={getToggleButtonProps} 
          />
        </div>

        {isLoadingState && (
          <LoadingSpinner hasSelection={!!selectedBranch} />
        )}
      </div>

      <BranchDropdownMenu
        isOpen={isOpen}
        filteredBranches={filteredBranches}
        isLoadingState={isLoadingState}
        inputValue={inputValue}
        highlightedIndex={highlightedIndex}
        selectedItem={selectedItem}
        isFetchingNextPage={isFetchingNextPage}
        getMenuProps={getMenuProps}
        getItemProps={getItemProps}
        onScroll={handleMenuScroll}
        menuRef={menuRef}
      />

      <ErrorMessage isError={!!error} />
    </div>
  );
}