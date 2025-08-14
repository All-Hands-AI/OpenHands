import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useCombobox } from "downshift";
import { Provider } from "../../types/settings";
import { useGitRepositories } from "../../hooks/query/use-git-repositories";
import { useSearchRepositories } from "../../hooks/query/use-search-repositories";
import { useDebounce } from "../../hooks/use-debounce";
import { GitRepository } from "../../types/git";

export interface GitRepositoryDropdownProps {
  provider: Provider;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  onChange?: (repository?: GitRepository) => void;
}

interface RepositoryOption {
  value: string;
  label: string;
  data: GitRepository;
}

export function GitRepositoryDropdown({
  provider,
  value,
  placeholder = "Search repositories...",
  className = "",
  errorMessage,
  disabled = false,
  onChange,
}: GitRepositoryDropdownProps) {
  const { t } = useTranslation();
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearchInput = useDebounce(searchInput, 300);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Process search input to handle URLs
  const processedSearchInput = useMemo(() => {
    if (debouncedSearchInput.startsWith("https://")) {
      const url = new URL(debouncedSearchInput);
      const pathParts = url.pathname.split("/").filter(Boolean);
      if (pathParts.length >= 2) {
        return `${pathParts[0]}/${pathParts[1]}`;
      }
    }
    return debouncedSearchInput;
  }, [debouncedSearchInput]);
  const lastSearchTimeRef = useRef<number>(0);
  const searchCacheRef = useRef<Map<string, AsyncSelectOption[]>>(new Map());


  // Process search input to handle URLs
  const processedSearchInput = useMemo(() => {
    if (debouncedSearchInput.startsWith("https://")) {
      const match = debouncedSearchInput.match(
        /https:\/\/[^/]+\/([^/]+\/[^/]+)/,
      );
      return match ? match[1] : debouncedSearchInput;
    }
    return debouncedSearchInput;
  }, [debouncedSearchInput]);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isLoading,
    isFetchingNextPage,
    isError,
  } = useGitRepositories({
    provider,
    enabled: !disabled,
  });

  // Search query for processed input (handles URLs)
  const { data: searchData, isLoading: isSearchLoading } =
    useSearchRepositories(processedSearchInput, provider);

  const allOptions: AsyncSelectOption[] = useMemo(
    () =>
      data?.pages
        ? data.pages.flatMap((page) =>
            page.data.map((repo) => ({
              value: repo.full_name,
              label: repo.full_name,
              data: repo,
            })),
          )
        : [],
    [data],
  );

  const searchOptions: AsyncSelectOption[] = useMemo(
    () => {
      const options = searchData
        ? searchData.map((repo) => ({
            value: repo.full_name,
            label: repo.full_name,
            data: repo,
          }))
        : [];
      
      console.log('searchOptions updated:', {
        searchDataLength: searchData?.length || 0,
        optionsLength: options.length,
        processedSearchInput,
        options: options.slice(0, 3) // Show first 3 for debugging
      });
      
      return options;
    },
    [searchData, processedSearchInput],
  );

  // loadOptions with proper debouncing that waits
  const loadOptions = useCallback(
    async (inputValue: string): Promise<AsyncSelectOption[]> => {
      console.log('loadOptions called:', { inputValue, searchOptionsLength: searchOptions.length });
      
      // If no input or short input, return paginated results
      if (!inputValue || inputValue.length < 2) {
        console.log('Returning paginated results (short input):', allOptions.length);
        return allOptions;
      }
      
      // Check cache first
      const cached = searchCacheRef.current.get(inputValue);
      if (cached) {
        console.log('Returning cached results:', cached.length);
        return cached;
      }
      
      // If we already have search results for this exact input from hook, return them
      if (inputValue === processedSearchInput && searchOptions.length > 0) {
        console.log('Returning hook search results:', searchOptions.length);
        searchCacheRef.current.set(inputValue, searchOptions);
        return searchOptions;
      }
      
      // Debouncing logic - wait if needed
      const now = Date.now();
      const timeSinceLastSearch = now - lastSearchTimeRef.current;
      const isSameSearch = inputValue === lastSearchRef.current;
      
      if (!isSameSearch && timeSinceLastSearch < 300) {
        const waitTime = 300 - timeSinceLastSearch;
        console.log(`Debouncing: waiting ${waitTime}ms before search`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
      
      // Update refs and do the search
      lastSearchRef.current = inputValue;
      lastSearchTimeRef.current = Date.now();
      
      try {
        console.log('Doing debounced direct search for:', inputValue);
        const repositories = await OpenHands.searchGitRepositories(inputValue, 10, provider);
        const directResults = repositories.map((repo) => ({
          value: repo.full_name,
          label: repo.full_name,
          data: repo,
        }));
        console.log('Direct search results:', directResults.length);
        
        // Cache the results
        searchCacheRef.current.set(inputValue, directResults);
        return directResults;
      } catch (error) {
        console.log('Direct search failed, falling back to local filter:', error);
        // Fall back to local filtering
        const filtered = allOptions.filter((option) =>
          option.label.toLowerCase().includes(inputValue.toLowerCase())
        );
        return filtered;
      }
    },
    [searchOptions, allOptions, processedSearchInput, provider]
  );



  const selectedOption = useMemo(() => {
    // First check in loaded pages
    const option = allOptions.find((opt) => opt.value === value);
    if (option) return option;

    // If not found, check in search results
    const searchOption = searchOptions.find((opt) => opt.value === value);
    if (searchOption) return searchOption;

    return null;
  }, [allOptions, searchOptions, value]);



  const handleChange = (option: AsyncSelectOption | null) => {
    if (!option) {
      onChange?.(undefined);
      return;
    }

    // First check in loaded pages
    let repo = data?.pages
      ?.flatMap((p) => p.data)
      .find((r) => r.id === option.value);

    // If not found, check in search results
    if (!repo) {
      repo = searchData?.find((r) => r.id === option.value);
    }

    onChange?.(repo);
  };

  const handleMenuScrollToBottom = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage && !isLoading) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, isLoading, fetchNextPage]);

  return (
    <>
      <ReactSelectAsyncDropdown
        testId="repo-dropdown"
        loadOptions={loadOptions}
        value={selectedOption}
        placeholder={placeholder}
        className={className}
        errorMessage={errorMessage}
        disabled={disabled}
        isClearable={false}
        isLoading={isLoading || isFetchingNextPage || isSearchLoading}
        cacheOptions={false}
        defaultOptions={allOptions}
        onChange={handleChange}
        onMenuScrollToBottom={handleMenuScrollToBottom}
      />
      {isError && (
        <div
          data-testid="repo-dropdown-error"
          className="text-red-500 text-sm mt-1"
        >
          {t("HOME$FAILED_TO_LOAD_REPOSITORIES")}
        </div>
      )}
    </>
  );
}
