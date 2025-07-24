import { useState, useCallback } from "react";
import { Provider } from "../../types/settings";
import { useGitRepositories } from "../../hooks/query/use-git-repositories";
import {
  InfiniteScrollAutocomplete,
  AutocompleteOption,
} from "./infinite-scroll-autocomplete";

export interface GitRepositoryAutocompleteProps {
  provider: Provider;
  label?: string;
  placeholder?: string;
  defaultSelectedKey?: string;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  onSelectionChange?: (key: React.Key | null) => void;
}

export function GitRepositoryAutocomplete({
  provider,
  label = "Select Repository",
  placeholder = "Search repositories...",
  defaultSelectedKey,
  className,
  errorMessage,
  disabled = false,
  onSelectionChange,
}: GitRepositoryAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { data, fetchNextPage, hasNextPage, isLoading } = useGitRepositories({
    provider,
    enabled: !disabled,
  });

  const items: AutocompleteOption[] =
    data?.pages.flatMap((page) =>
      page.data.map((repo) => ({
        key: repo.id,
        value: repo.full_name,
      })),
    ) ?? [];

  const handleLoadMore = useCallback(() => {
    fetchNextPage();
  }, [fetchNextPage]);

  const handleOpenChange = useCallback(
    (open: boolean) => {
      if (!disabled) {
        setIsOpen(open);
      }
    },
    [disabled],
  );

  return (
    <InfiniteScrollAutocomplete
      items={items}
      label={label}
      placeholder={placeholder}
      defaultSelectedKey={defaultSelectedKey}
      className={className}
      errorMessage={errorMessage}
      isLoading={isLoading}
      hasMore={hasNextPage}
      isOpen={isOpen}
      onOpenChange={handleOpenChange}
      onLoadMore={handleLoadMore}
      onSelectionChange={onSelectionChange}
    />
  );
}
