import React, {
  useState,
  useMemo,
  useCallback,
  useRef,
  useEffect,
} from "react";
import { useCombobox } from "downshift";
import { Provider } from "#/types/settings";
import { GitRepository } from "#/types/git";
import { useDebounce } from "#/hooks/use-debounce";
import { cn } from "#/utils/utils";
import { LoadingSpinner } from "../shared/loading-spinner";
import { ClearButton } from "../shared/clear-button";
import { ToggleButton } from "../shared/toggle-button";
import { ErrorMessage } from "../shared/error-message";
import { useUrlSearch } from "./use-url-search";
import { useRepositoryData } from "./use-repository-data";
import { DropdownMenu } from "./dropdown-menu";

export interface GitRepoDropdownProps {
  provider: Provider;
  value?: string | null;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  onChange?: (repository?: GitRepository) => void;
}

export function GitRepoDropdown({
  provider,
  value,
  placeholder = "Search repositories...",
  className,
  disabled = false,
  onChange,
}: GitRepoDropdownProps) {
  const [inputValue, setInputValue] = useState("");
  const [localSelectedItem, setLocalSelectedItem] =
    useState<GitRepository | null>(null);
  const debouncedInputValue = useDebounce(inputValue, 300);
  const menuRef = useRef<HTMLUListElement>(null);

  // Process search input to handle URLs
  const processedSearchInput = useMemo(() => {
    if (debouncedInputValue.startsWith("https://")) {
      const match = debouncedInputValue.match(
        /https:\/\/[^/]+\/([^/]+\/[^/]+)/,
      );
      return match ? match[1] : debouncedInputValue;
    }
    return debouncedInputValue;
  }, [debouncedInputValue]);

  // URL search functionality
  const { urlSearchResults, isUrlSearchLoading } = useUrlSearch(
    inputValue,
    provider,
  );

  // Repository data management
  const {
    repositories,
    selectedRepository,
    fetchNextPage,
    hasNextPage,
    isLoading,
    isFetchingNextPage,
    isError,
    isSearchLoading,
  } = useRepositoryData(
    provider,
    disabled,
    processedSearchInput,
    urlSearchResults,
    inputValue,
    value,
  );

  // Filter repositories based on input value
  const filteredRepositories = useMemo(() => {
    // If we have URL search results, show them directly (no filtering needed)
    if (urlSearchResults.length > 0) {
      return repositories;
    }

    // If we have a selected repository and the input matches it exactly, show all repositories
    if (selectedRepository && inputValue === selectedRepository.full_name) {
      return repositories;
    }

    // If no input value, show all repositories
    if (!inputValue || !inputValue.trim()) {
      return repositories;
    }

    // For URL inputs, use the processed search input for filtering
    const filterText = inputValue.startsWith("https://")
      ? processedSearchInput
      : inputValue;

    return repositories.filter((repo) =>
      repo.full_name.toLowerCase().includes(filterText.toLowerCase()),
    );
  }, [
    repositories,
    inputValue,
    selectedRepository,
    urlSearchResults,
    processedSearchInput,
  ]);

  // Handle selection
  const handleSelectionChange = useCallback(
    (selectedItem: GitRepository | null) => {
      setLocalSelectedItem(selectedItem);
      onChange?.(selectedItem || undefined);
      // Update input value to show selected item
      if (selectedItem) {
        setInputValue(selectedItem.full_name);
      }
    },
    [onChange],
  );

  // Handle clear selection
  const handleClear = useCallback(() => {
    setLocalSelectedItem(null);
    handleSelectionChange(null);
    setInputValue("");
  }, [handleSelectionChange]);

  // Handle input value change
  const handleInputValueChange = useCallback(
    ({ inputValue: newInputValue }: { inputValue?: string }) => {
      setInputValue(newInputValue || "");
    },
    [],
  );

  // Handle scroll to bottom for pagination
  const handleMenuScroll = useCallback(
    (event: React.UIEvent<HTMLUListElement>) => {
      const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
      const isNearBottom = scrollTop + clientHeight >= scrollHeight - 10;

      if (isNearBottom && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [hasNextPage, isFetchingNextPage, fetchNextPage],
  );

  const {
    isOpen,
    getToggleButtonProps,
    getMenuProps,
    getInputProps,
    highlightedIndex,
    getItemProps,
    selectedItem,
  } = useCombobox({
    items: filteredRepositories,
    itemToString: (item) => item?.full_name || "",
    selectedItem: localSelectedItem,
    onSelectedItemChange: ({ selectedItem: newSelectedItem }) => {
      handleSelectionChange(newSelectedItem);
    },
    onInputValueChange: handleInputValueChange,
    inputValue,
  });

  // Sync localSelectedItem with external value prop
  useEffect(() => {
    if (selectedRepository) {
      setLocalSelectedItem(selectedRepository);
    } else if (value === null) {
      setLocalSelectedItem(null);
    }
  }, [selectedRepository, value]);

  // Initialize input value when selectedRepository changes (but not when user is typing)
  useEffect(() => {
    if (selectedRepository && !isOpen) {
      setInputValue(selectedRepository.full_name);
    }
  }, [selectedRepository, isOpen]);

  const isLoadingState =
    isLoading || isSearchLoading || isFetchingNextPage || isUrlSearchLoading;

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <input
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...getInputProps({
            disabled,
            placeholder,
            className: cn(
              "w-full px-3 py-2 border border-[#717888] rounded-sm shadow-sm min-h-[2.5rem]",
              "bg-[#454545] text-[#ECEDEE] placeholder:text-[#B7BDC2] placeholder:italic",
              "focus:outline-none focus:ring-1 focus:ring-[#717888] focus:border-[#717888]",
              "disabled:bg-[#363636] disabled:cursor-not-allowed disabled:opacity-60",
              "pr-10", // Space for toggle button
            ),
          })}
          data-testid="git-repo-dropdown"
        />

        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
          {selectedRepository && (
            <ClearButton disabled={disabled} onClear={handleClear} />
          )}

          <ToggleButton
            isOpen={isOpen}
            disabled={disabled}
            getToggleButtonProps={getToggleButtonProps}
          />
        </div>

        {isLoadingState && (
          <LoadingSpinner hasSelection={!!selectedRepository} />
        )}
      </div>

      <DropdownMenu
        isOpen={isOpen}
        filteredRepositories={filteredRepositories}
        inputValue={inputValue}
        highlightedIndex={highlightedIndex}
        selectedItem={selectedItem}
        getMenuProps={getMenuProps}
        getItemProps={getItemProps}
        onScroll={handleMenuScroll}
        menuRef={menuRef}
      />

      <ErrorMessage isError={isError} />
    </div>
  );
}
