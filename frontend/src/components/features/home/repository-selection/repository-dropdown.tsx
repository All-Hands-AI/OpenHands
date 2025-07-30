import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../../settings/settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

export interface RepositoryDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
  defaultFilter?: (textValue: string, inputValue: string) => boolean;
  wrapperClassName?: string;
}

export function RepositoryDropdown({
  items,
  onSelectionChange,
  onInputChange,
  defaultFilter,
  wrapperClassName,
}: RepositoryDropdownProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="repo-dropdown"
      name="repo-dropdown"
      placeholder={t(I18nKey.REPOSITORY$SELECT_REPO)}
      items={items}
      wrapperClassName={cn("max-w-[500px]", wrapperClassName)}
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
      defaultFilter={defaultFilter}
    />
  );
}
