import React, { useMemo, useRef, useCallback } from "react";
import Select, { components, MenuListProps } from "react-select";
import { cn } from "#/utils/utils";
import { SelectOptionBase, getCustomStyles } from "./react-select-styles";

export type SelectOption = SelectOptionBase;

export interface InfiniteScrollSelectProps {
  options: SelectOption[];
  placeholder?: string;
  value?: SelectOption | null;
  defaultValue?: SelectOption | null;
  className?: string;
  errorMessage?: string;
  disabled?: boolean;
  isClearable?: boolean;
  isSearchable?: boolean;
  isLoading?: boolean;
  hasNextPage?: boolean;
  onLoadMore?: () => void;
  onChange?: (option: SelectOption | null) => void;
  onInputChange?: (inputValue: string) => void;
}

function MenuList({
  children,
  selectProps,
  ...otherProps
}: MenuListProps<SelectOption>) {
  const { hasNextPage, onLoadMore } =
    selectProps as unknown as InfiniteScrollSelectProps;

  const observer = useRef<IntersectionObserver | null>(null);

  const lastElementRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (observer.current) observer.current.disconnect();
      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage && onLoadMore) {
          onLoadMore();
        }
      });
      if (node) observer.current.observe(node);
    },
    [hasNextPage, onLoadMore],
  );

  return (
    // eslint-disable-next-line react/jsx-props-no-spreading
    <components.MenuList selectProps={selectProps} {...otherProps}>
      {children}
      {hasNextPage && (
        <div
          ref={lastElementRef}
          className="px-3 py-2 text-sm text-gray-500 text-center"
        >
          Loading more...
        </div>
      )}
    </components.MenuList>
  );
}

export function InfiniteScrollSelect({
  options,
  placeholder = "Select option...",
  value,
  defaultValue,
  className,
  errorMessage,
  disabled = false,
  isClearable = false,
  isSearchable = true,
  isLoading = false,
  hasNextPage = false,
  onLoadMore,
  onChange,
  onInputChange,
}: InfiniteScrollSelectProps) {
  const customStyles = useMemo(() => getCustomStyles<SelectOption>(), []);

  return (
    <div className={cn("w-full", className)}>
      <Select
        options={options}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        isDisabled={disabled}
        isClearable={isClearable}
        isSearchable={isSearchable}
        isLoading={isLoading}
        onChange={onChange}
        onInputChange={(newValue) => onInputChange?.(newValue)}
        styles={customStyles}
        className="w-full"
        components={{ MenuList }}
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...({ hasNextPage, onLoadMore } as unknown as Record<string, unknown>)}
      />
      {errorMessage && (
        <p className="text-red-500 text-sm mt-1">{errorMessage}</p>
      )}
    </div>
  );
}
