import { Autocomplete, AutocompleteItem } from "@heroui/react";
import { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { OptionalTag } from "./optional-tag";
import { cn } from "#/utils/utils";
import React from "react";
import { useInfiniteScroll } from "@heroui/use-infinite-scroll";

interface SettingsDropdownInputProps {
  testId: string;
  name: string;
  items: { key: React.Key; label: string }[];
  label?: ReactNode;
  wrapperClassName?: string;
  placeholder?: string;
  showOptionalTag?: boolean;
  isDisabled?: boolean;
  isLoading?: boolean;
  isFetchingNextPage?: boolean;
  defaultSelectedKey?: string;
  selectedKey?: string;
  isClearable?: boolean;
  allowsCustomValue?: boolean;
  required?: boolean;
  onSelectionChange?: (key: React.Key | null) => void;
  onInputChange?: (value: string) => void;
  defaultFilter?: (textValue: string, inputValue: string) => boolean;
  // Infinite scroll props
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export function SettingsDropdownInput({
  testId,
  label,
  wrapperClassName,
  name,
  items,
  placeholder,
  showOptionalTag,
  isDisabled,
  isLoading,
  isFetchingNextPage,
  defaultSelectedKey,
  selectedKey,
  isClearable,
  allowsCustomValue,
  required,
  onSelectionChange,
  onInputChange,
  defaultFilter,
  hasMore,
  onLoadMore,
}: SettingsDropdownInputProps) {
  const { t } = useTranslation();

  const [isOpen, setIsOpen] = React.useState(false);

  const [, scrollerRef] = useInfiniteScroll({
    hasMore,
    isEnabled: isOpen,
    shouldUseLoader: false,
    onLoadMore,
  });

  return (
    <label className={cn("flex flex-col gap-2.5", wrapperClassName)}>
      {label && (
        <div className="flex items-center gap-1">
          <span className="text-sm">{label}</span>
          {showOptionalTag && <OptionalTag />}
        </div>
      )}
      <Autocomplete
        aria-label={typeof label === "string" ? label : name}
        data-testid={testId}
        name={name}
        defaultItems={items}
        defaultSelectedKey={defaultSelectedKey}
        selectedKey={selectedKey}
        onSelectionChange={onSelectionChange}
        onInputChange={onInputChange}
        isClearable={isClearable}
        isDisabled={isDisabled || isLoading}
        isLoading={isLoading || isFetchingNextPage}
        placeholder={isLoading ? t("HOME$LOADING") : placeholder}
        allowsCustomValue={allowsCustomValue}
        isRequired={required}
        className="w-full"
        classNames={{
          popoverContent: "bg-tertiary rounded-xl border border-[#717888]",
        }}
        inputProps={{
          classNames: {
            inputWrapper:
              "bg-tertiary border border-[#717888] h-10 w-full rounded-sm p-2 placeholder:italic",
          },
        }}
        scrollRef={scrollerRef}
        defaultFilter={defaultFilter}
        onOpenChange={setIsOpen}
      >
        {(item) => (
          <AutocompleteItem key={item.key}>{item.label}</AutocompleteItem>
        )}
      </Autocomplete>
    </label>
  );
}
