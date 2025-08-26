import React, { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { useCombobox } from "downshift";
import { useTranslation } from "react-i18next";
import { Provider } from "#/types/settings";
import { GitRepository } from "#/types/git";
import { useGitRepositories } from "#/hooks/query/use-git-repositories";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useDebounce } from "#/hooks/use-debounce";
import { cn } from "#/utils/utils";
import OpenHands from "#/api/open-hands";

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
  const { t } = useTranslation();
  const [inputValue, setInputValue] = useState("");
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

  // Fetch user repositories with pagination
  const {
    data: repoData,
    fetchNextPage,
    hasNextPage,
    isLoading,
    isFetchingNextPage,
    isError,
  } = useGitRepositories({
    provider,
    enabled: !disabled,
  });

  // Search repositories when user types
  const { data: searchData, isLoading: isSearchLoading } =
    useSearchRepositories(processedSearchInput, provider);

  // Handle direct URL search for immediate results
  const [urlSearchResults, setUrlSearchResults] = useState<GitRepository[]>([]);
  const [isUrlSearchLoading, setIsUrlSearchLoading] = useState(false);

  useEffect(() => {
    const handleUrlSearch = async () => {
      if (inputValue.startsWith("https://")) {
        const match = inputValue.match(/https:\/\/[^/]+\/([^/]+\/[^/]+)/);
        if (match) {
          const repoName = match[1];
          console.log("URL detected, searching for:", repoName);
          setIsUrlSearchLoading(true);
          try {
            const repositories = await OpenHands.searchGitRepositories(
              repoName,
              3,
              provider,
            );
            console.log("URL search results:", repositories);
            setUrlSearchResults(repositories);
          } catch (error) {
            console.error("URL search failed:", error);
            setUrlSearchResults([]);
          } finally {
            setIsUrlSearchLoading(false);
          }
        }
      } else {
        setUrlSearchResults([]);
      }
    };

    handleUrlSearch();
  }, [inputValue, provider]);

  // Combine all repositories from paginated data
  const allRepositories = useMemo(() => {
    return repoData?.pages?.flatMap((page) => page.data) || [];
  }, [repoData]);

  // Find selected repository from all repositories (not filtered)
  const selectedRepository = useMemo(() => {
    return allRepositories.find((repo) => repo.id === value) || null;
  }, [allRepositories, value]);

  // Get repositories to display (URL search, regular search, or all repos)
  const repositories = useMemo(() => {
    // Prioritize URL search results when available
    if (urlSearchResults.length > 0) {
      return urlSearchResults;
    }
    
    // Don't use search results if input exactly matches selected repository
    const shouldUseSearch = processedSearchInput && 
      searchData && 
      !(selectedRepository && inputValue === selectedRepository.full_name);
    
    if (shouldUseSearch) {
      return searchData;
    }
    return allRepositories;
  }, [urlSearchResults, processedSearchInput, searchData, allRepositories, selectedRepository, inputValue]);

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
    const filterText = inputValue.startsWith("https://") ? processedSearchInput : inputValue;
    
    return repositories.filter((repo) =>
      repo.full_name.toLowerCase().includes(filterText.toLowerCase())
    );
  }, [repositories, inputValue, selectedRepository, urlSearchResults, processedSearchInput]);

  // Handle selection
  const handleSelectionChange = useCallback(
    (selectedItem: GitRepository | null) => {
      onChange?.(selectedItem || undefined);
      // Update input value to show selected item
      if (selectedItem) {
        setInputValue(selectedItem.full_name);
      }
    },
    [onChange]
  );

  // Handle input value change
  const handleInputValueChange = useCallback(
    ({ inputValue: newInputValue }: { inputValue?: string }) => {
      setInputValue(newInputValue || "");
    },
    []
  );

  // Handle scroll to bottom for pagination
  const handleMenuScroll = useCallback(
    (event: React.UIEvent<HTMLUListElement>) => {
      const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
      const isNearBottom = scrollTop + clientHeight >= scrollHeight - 10;
      
      if (isNearBottom && hasNextPage && !isFetchingNextPage && !isLoading) {
        fetchNextPage();
      }
    },
    [hasNextPage, isFetchingNextPage, isLoading, fetchNextPage]
  );

  const {
    isOpen,
    getToggleButtonProps,
    getLabelProps,
    getMenuProps,
    getInputProps,
    highlightedIndex,
    getItemProps,
    selectedItem,
    reset,
  } = useCombobox({
    items: filteredRepositories,
    itemToString: (item) => item?.full_name || "",
    selectedItem: selectedRepository,
    onSelectedItemChange: ({ selectedItem }) => {
      handleSelectionChange(selectedItem);
    },
    onInputValueChange: handleInputValueChange,
    inputValue,
  });

  // Initialize input value when selectedRepository changes (but not when user is typing)
  useEffect(() => {
    if (selectedRepository && !isOpen && inputValue !== selectedRepository.full_name) {
      setInputValue(selectedRepository.full_name);
    } else if (!selectedRepository && !isOpen && inputValue) {
      setInputValue("");
    }
  }, [selectedRepository, isOpen]);

  const isLoadingState = isLoading || isSearchLoading || isFetchingNextPage || isUrlSearchLoading;

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <input
          {...getInputProps({
            disabled,
            placeholder,
            className: cn(
              "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "disabled:bg-gray-100 disabled:cursor-not-allowed",
              "pr-10" // Space for toggle button
            ),
          })}
          data-testid="git-repo-dropdown"
        />
        
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
          {selectedRepository && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleSelectionChange(null);
                setInputValue("");
              }}
              disabled={disabled}
              className={cn(
                "p-1 text-gray-400 hover:text-gray-600",
                "disabled:cursor-not-allowed"
              )}
              type="button"
              aria-label="Clear selection"
              data-testid="git-repo-dropdown-clear"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
          
          <button
            {...getToggleButtonProps({
              disabled,
              className: cn(
                "p-1 text-gray-400 hover:text-gray-600",
                "disabled:cursor-not-allowed"
              ),
            })}
            type="button"
            aria-label="Toggle menu"
          >
            <svg
              className={cn(
                "w-4 h-4 transition-transform",
                isOpen && "rotate-180"
              )}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        {isLoadingState && (
          <div className={cn(
            "absolute top-1/2 transform -translate-y-1/2",
            selectedRepository ? "right-16" : "right-12"
          )}>
            <div
              className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"
              data-testid="git-repo-dropdown-loading"
            />
          </div>
        )}
      </div>

      <ul
        {...getMenuProps({
          ref: menuRef,
          onScroll: handleMenuScroll,
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
              <li
                className="px-3 py-2 text-gray-500 text-sm"
                data-testid="git-repo-dropdown-empty"
              >
                {inputValue ? "No repositories found" : "No repositories available"}
              </li>
            )}
            
            {filteredRepositories.map((repository, index) => (
              <li
                key={repository.id}
                {...getItemProps({
                  item: repository,
                  index,
                  className: cn(
                    "px-3 py-2 cursor-pointer text-sm",
                    "hover:bg-blue-50",
                    highlightedIndex === index && "bg-blue-100",
                    selectedItem?.id === repository.id && "bg-blue-200"
                  ),
                })}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{repository.full_name}</span>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    {repository.is_public ? (
                      <span className="text-green-600">Public</span>
                    ) : (
                      <span className="text-orange-600">Private</span>
                    )}
                    {repository.stargazers_count > 0 && (
                      <span>⭐ {repository.stargazers_count}</span>
                    )}
                  </div>
                </div>
              </li>
            ))}
            
            {isFetchingNextPage && (
              <li className="px-3 py-2 text-center text-sm text-gray-500">
                Loading more repositories...
              </li>
            )}
          </>
        )}
      </ul>

      {isError && (
        <div
          className="text-red-500 text-sm mt-1"
          data-testid="git-repo-dropdown-error"
        >
          {t("HOME$FAILED_TO_LOAD_REPOSITORIES")}
        </div>
      )}
    </div>
  );
}