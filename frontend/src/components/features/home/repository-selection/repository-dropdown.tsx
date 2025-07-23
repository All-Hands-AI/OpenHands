import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../../settings/settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";

export interface RepositoryDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
  defaultFilter?: (textValue: string, inputValue: string) => boolean;
  isDisabled?: boolean;
  // Infinite scroll props
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
  onLoadMore?: () => void;
}

export function RepositoryDropdown({
  items,
  onSelectionChange,
  onInputChange,
  defaultFilter,
  isDisabled = false,
  hasNextPage,
  isFetchingNextPage,
  onLoadMore,
}: RepositoryDropdownProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="repo-dropdown"
      name="repo-dropdown"
      placeholder={
        isDisabled
          ? t("Please select a provider first")
          : t(I18nKey.REPOSITORY$SELECT_REPO)
      }
      items={items}
      wrapperClassName="max-w-[500px]"
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
      defaultFilter={defaultFilter}
      isDisabled={isDisabled}
      isLoading={isFetchingNextPage}
      hasNextPage={hasNextPage}
      isFetchingNextPage={isFetchingNextPage}
      onLoadMore={onLoadMore}
    />
  );
}
