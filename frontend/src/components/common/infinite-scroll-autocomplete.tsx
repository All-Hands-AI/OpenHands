import { Autocomplete, AutocompleteItem } from "@heroui/react";
import { useInfiniteScroll } from "@heroui/use-infinite-scroll";
import { useCallback } from "react";

export interface AutocompleteOption {
  key: string;
  value: string;
}

export interface InfiniteScrollAutocompleteProps {
  items: AutocompleteOption[];
  label?: string;
  placeholder?: string;
  isLoading?: boolean;
  hasMore?: boolean;
  isOpen?: boolean;
  defaultSelectedKey?: string;
  className?: string;
  errorMessage?: string;
  onLoadMore?: () => void;
  onSelectionChange?: (key: React.Key | null) => void;
  onOpenChange?: (isOpen: boolean) => void;
}

export function InfiniteScrollAutocomplete({
  items,
  label,
  placeholder,
  isLoading,
  hasMore = false,
  isOpen = false,
  defaultSelectedKey,
  className,
  errorMessage,
  onLoadMore,
  onSelectionChange,
  onOpenChange,
}: InfiniteScrollAutocompleteProps) {
  const [, scrollerRef] = useInfiniteScroll({
    hasMore,
    isEnabled: isOpen,
    shouldUseLoader: false,
    onLoadMore,
  });

  const handleSelectionChange = useCallback(
    (key: React.Key | null) => {
      onSelectionChange?.(key);
    },
    [onSelectionChange],
  );

  return (
    <Autocomplete
      label={label}
      placeholder={placeholder}
      isLoading={isLoading}
      defaultSelectedKey={defaultSelectedKey}
      className={className}
      errorMessage={errorMessage}
      scrollRef={scrollerRef}
      onSelectionChange={handleSelectionChange}
      onOpenChange={onOpenChange}
      listboxProps={{
        className: "max-h-[300px] overflow-auto",
      }}
    >
      {items.map((item) => (
        <AutocompleteItem key={item.key} value={item.key}>
          {item.value}
        </AutocompleteItem>
      ))}
    </Autocomplete>
  );
}
