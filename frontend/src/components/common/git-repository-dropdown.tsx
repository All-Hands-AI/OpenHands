import { useCallback, useMemo } from "react";
import { Provider } from "../../types/settings";
import { useGitRepositories } from "../../hooks/query/use-git-repositories";
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

export function GitRepositoryDropdown({
  provider,
  value,
  placeholder = "Search repositories...",
  className,
  errorMessage,
  disabled = false,
  onChange,
}: GitRepositoryDropdownProps) {
  const { data, fetchNextPage, hasNextPage, isLoading, isFetchingNextPage } =
    useGitRepositories({
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

  const selectedOption = useMemo(
    () => allOptions.find((option) => option.value === value) || null,
    [allOptions, value],
  );

  const loadOptions = useCallback(
    (inputValue: string): Promise<AsyncSelectOption[]> => {
      const filteredOptions = allOptions.filter((option) =>
        option.label.toLowerCase().includes(inputValue.toLowerCase()),
      );
      return Promise.resolve(filteredOptions);
    },
    [allOptions],
  );

  const handleChange = (option: AsyncSelectOption | null) => {
    const repo = data?.pages
      ?.flatMap((p) => p.data)
      .find((r) => r.id === option?.value);
    onChange?.(repo);
  };

  const handleMenuScrollToBottom = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage && !isLoading) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, isLoading, fetchNextPage]);

  return (
    <ReactSelectAsyncDropdown
      loadOptions={loadOptions}
      value={selectedOption}
      placeholder={placeholder}
      className={className}
      errorMessage={errorMessage}
      disabled={disabled}
      isClearable={false}
      cacheOptions
      defaultOptions={allOptions}
      onChange={handleChange}
      onMenuScrollToBottom={handleMenuScrollToBottom}
    />
  );
}
