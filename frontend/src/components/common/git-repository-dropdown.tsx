import { StylesConfig } from "react-select";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Provider } from "../../types/settings";
import { useGitRepositories } from "../../hooks/query/use-git-repositories";
import { useSearchRepositories } from "../../hooks/query/use-search-repositories";
import { useDebounce } from "../../hooks/use-debounce";
import OpenHands from "../../api/open-hands";
import { GitRepository } from "../../types/git";
import {
  ReactSelectAsyncDropdown,
  AsyncSelectOption,
} from "./react-select-async-dropdown";
import RepoIcon from "#/icons/repo.svg?react";
import { SelectOption } from "./react-select-styles";
import { ReactSelectCustomControl } from "./react-select-custom-control";

export interface GitRepositoryDropdownProps {
  provider: Provider;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  onChange?: (repository?: GitRepository) => void;
  styles?: StylesConfig<SelectOption, false>;
  classNamePrefix?: string;
}

export function GitRepositoryDropdown({
  provider,
  value,
  placeholder = "Search repositories...",
  className,
  errorMessage,
  disabled = false,
  onChange,
  styles,
  classNamePrefix,
}: GitRepositoryDropdownProps) {
  const { t } = useTranslation();
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearchInput = useDebounce(searchInput, 300);

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
              value: repo.id,
              label: repo.full_name,
            })),
          )
        : [],
    [data],
  );

  const searchOptions: AsyncSelectOption[] = useMemo(
    () =>
      searchData
        ? searchData.map((repo) => ({
            value: repo.id,
            label: repo.full_name,
          }))
        : [],
    [searchData],
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

  const loadOptions = useCallback(
    async (inputValue: string): Promise<AsyncSelectOption[]> => {
      // Update search input to trigger debounced search
      setSearchInput(inputValue);

      // If empty input, show all loaded options
      if (!inputValue.trim()) {
        return allOptions;
      }

      // For very short inputs, do local filtering
      if (inputValue.length < 2) {
        return allOptions.filter((option) =>
          option.label.toLowerCase().includes(inputValue.toLowerCase()),
        );
      }

      // Handle URL inputs by performing direct search
      if (inputValue.startsWith("https://")) {
        const match = inputValue.match(/https:\/\/[^/]+\/([^/]+\/[^/]+)/);
        if (match) {
          const repoName = match[1];
          try {
            // Perform direct search for URL-based inputs
            const repositories = await OpenHands.searchGitRepositories(
              repoName,
              3,
              provider,
            );
            return repositories.map((repo) => ({
              value: repo.full_name,
              label: repo.full_name,
              data: repo,
            }));
          } catch (error) {
            // Fall back to local filtering if search fails
            return allOptions.filter((option) =>
              option.label.toLowerCase().includes(repoName.toLowerCase()),
            );
          }
        }
      }

      // For regular text inputs, use hook-based search results if available
      if (searchOptions.length > 0 && processedSearchInput === inputValue) {
        return searchOptions;
      }

      // Fallback to local filtering while search is loading
      return allOptions.filter((option) =>
        option.label.toLowerCase().includes(inputValue.toLowerCase()),
      );
    },
    [allOptions, searchOptions, processedSearchInput, provider],
  );

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
        cacheOptions
        defaultOptions={allOptions}
        onChange={handleChange}
        onMenuScrollToBottom={handleMenuScrollToBottom}
        styles={styles}
        classNamePrefix={classNamePrefix}
        components={{
          IndicatorSeparator: () => null,
          Control: (props) => (
            <ReactSelectCustomControl
              {...props}
              startIcon={<RepoIcon width={16} height={16} />}
            />
          ),
        }}
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
