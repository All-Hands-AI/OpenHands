import { useCallback, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Provider } from "../../types/settings";
import { useGitRepositories } from "../../hooks/query/use-git-repositories";
import OpenHands from "../../api/open-hands";
import { GitRepository } from "../../types/git";
import {
  ReactSelectAsyncDropdown,
  AsyncSelectOption,
} from "./react-select-async-dropdown";

export interface GitRepositoryDropdownProps {
  provider: Provider;
  value?: string | null;
  placeholder?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  onChange?: (repository?: any) => void;
}

interface SearchCache {
  [key: string]: GitRepository[];
}

export function GitRepositoryDropdown({
  provider,
  value,
  placeholder = "Search repositories...",
  className,
  errorMessage,
  disabled = false,
  onChange,
}: GitRepositoryDropdownProps) {
  const { t } = useTranslation();
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

  // Keep track of search results
  const searchCache = useRef<SearchCache>({});

  const selectedOption = useMemo(() => {
    // First check in loaded pages
    const option = allOptions.find((opt) => opt.value === value);
    if (option) return option;

    // If not found, check in search cache
    const repo = Object.values(searchCache.current)
      .flat()
      .find((r) => r.id === value);

    if (repo) {
      return {
        value: repo.id,
        label: repo.full_name,
      };
    }

    return null;
  }, [allOptions, value]);

  const loadOptions = useCallback(
    async (inputValue: string): Promise<AsyncSelectOption[]> => {
      // If it looks like a URL, extract the repo name and search
      if (inputValue.startsWith("https://")) {
        const match = inputValue.match(/https:\/\/[^/]+\/([^/]+\/[^/]+)/);
        if (match) {
          const repoName = match[1];
          const searchResults = await OpenHands.searchGitRepositories(
            repoName,
            3,
          );
          // Cache the search results
          searchCache.current[repoName] = searchResults;
          return searchResults.map((repo) => ({
            value: repo.id,
            label: repo.full_name,
          }));
        }
      }

      // Otherwise do local filtering
      const filteredOptions = allOptions.filter((option) =>
        option.label.toLowerCase().includes(inputValue.toLowerCase()),
      );
      return filteredOptions;
    },
    [allOptions],
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
      repo = Object.values(searchCache.current)
        .flat()
        .find((r) => r.id === option.value);
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
        isLoading={isLoading || isLoading || isFetchingNextPage}
        cacheOptions
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
