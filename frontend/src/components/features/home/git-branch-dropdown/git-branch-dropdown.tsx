import React, {
  useState,
  useMemo,
  useCallback,
  useRef,
  useEffect,
} from "react";
import { useCombobox } from "downshift";
import { Branch } from "#/types/git";
import { Provider } from "#/types/settings";
import { useDebounce } from "#/hooks/use-debounce";
import { cn } from "#/utils/utils";
import { useBranchData } from "#/hooks/query/use-branch-data";
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
  defaultBranch?: string | null;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function GitBranchDropdown({
  repository,
  provider,
  selectedBranch,
  onBranchSelect,
  defaultBranch,
  placeholder = "Select branch...",
  disabled = false,
  className,
}: GitBranchDropdownProps) {
  const [inputValue, setInputValue] = useState("");
  const [userManuallyCleared, setUserManuallyCleared] = useState(false);
  const debouncedInputValue = useDebounce(inputValue, 300);
  const menuRef = useRef<HTMLUListElement>(null);

  // Process search input (debounced and filtered)
  const processedSearchInput = useMemo(
    () =>
      debouncedInputValue.trim().length > 0 ? debouncedInputValue.trim() : "",
    [debouncedInputValue],
  );

  // Use the new branch data hook with default branch prioritization
  const {
    branches: filteredBranches,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isSearchLoading,
  } = useBranchData(
    repository,
    provider,
    defaultBranch || null,
    processedSearchInput,
    inputValue,
    selectedBranch,
  );

  const error = isError ? new Error("Failed to load branches") : null;

  // Handle clear
  const handleClear = useCallback(() => {
    setInputValue("");
    onBranchSelect(null);
    setUserManuallyCleared(true); // Mark that user manually cleared the branch
  }, [onBranchSelect]);

  // Handle branch selection
  const handleBranchSelect = useCallback(
    (branch: Branch | null) => {
      onBranchSelect(branch);
      setInputValue("");
    },
    [onBranchSelect],
  );

  // Handle input value change
  const handleInputValueChange = useCallback(
    ({ inputValue: newInputValue }: { inputValue?: string }) => {
      if (newInputValue !== undefined) {
        setInputValue(newInputValue);
      }
    },
    [],
  );

  // Handle menu scroll for infinite loading
  const handleMenuScroll = useCallback(
    (event: React.UIEvent<HTMLUListElement>) => {
      const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
      if (
        scrollHeight - scrollTop <= clientHeight * 1.5 &&
        hasNextPage &&
        !isFetchingNextPage
      ) {
        fetchNextPage();
      }
    },
    [hasNextPage, isFetchingNextPage, fetchNextPage],
  );

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
    inputValue,
  });

  // Reset branch selection when repository changes
  useEffect(() => {
    if (repository) {
      onBranchSelect(null);
      setUserManuallyCleared(false); // Reset the manual clear flag when repository changes
    }
  }, [repository, onBranchSelect]);

  // Auto-select default branch when branches are loaded and no branch is selected
  // But only if the user hasn't manually cleared the branch
  useEffect(() => {
    if (
      repository &&
      defaultBranch &&
      !selectedBranch &&
      !userManuallyCleared && // Don't auto-select if user manually cleared
      filteredBranches.length > 0 &&
      !isLoading
    ) {
      const defaultBranchObj = filteredBranches.find(
        (branch) => branch.name === defaultBranch,
      );

      if (defaultBranchObj) {
        onBranchSelect(defaultBranchObj);
      }
    }
  }, [
    repository,
    defaultBranch,
    selectedBranch,
    userManuallyCleared,
    filteredBranches,
    onBranchSelect,
    isLoading,
  ]);

  // Reset input when repository changes
  useEffect(() => {
    setInputValue("");
  }, [repository]);

  // Initialize input value when selectedBranch changes (but not when user is typing)
  useEffect(() => {
    if (selectedBranch && !isOpen && inputValue !== selectedBranch.name) {
      setInputValue(selectedBranch.name);
    } else if (!selectedBranch && !isOpen && inputValue) {
      setInputValue("");
    }
  }, [selectedBranch, isOpen, inputValue]);

  const isLoadingState = isLoading || isSearchLoading || isFetchingNextPage;

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <input
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...getInputProps({
            disabled: disabled || !repository,
            placeholder,
            className: cn(
              "w-full px-3 py-2 border border-[#717888] rounded-sm shadow-sm min-h-[2.5rem]",
              "bg-[#454545] text-[#ECEDEE] placeholder:text-[#B7BDC2] placeholder:italic",
              "focus:outline-none focus:ring-1 focus:ring-[#717888] focus:border-[#717888]",
              "disabled:bg-[#363636] disabled:cursor-not-allowed disabled:opacity-60",
              "pr-10", // Space for toggle button
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

        {isLoadingState && <LoadingSpinner hasSelection={!!selectedBranch} />}
      </div>

      <BranchDropdownMenu
        isOpen={isOpen}
        filteredBranches={filteredBranches}
        inputValue={inputValue}
        highlightedIndex={highlightedIndex}
        selectedItem={selectedItem}
        getMenuProps={getMenuProps}
        getItemProps={getItemProps}
        onScroll={handleMenuScroll}
        menuRef={menuRef}
      />

      <ErrorMessage isError={!!error} />
    </div>
  );
}
