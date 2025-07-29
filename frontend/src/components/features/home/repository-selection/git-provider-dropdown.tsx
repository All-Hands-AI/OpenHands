import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../../settings/settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";

export interface GitProviderDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
  defaultFilter?: (textValue: string, inputValue: string) => boolean;
}

export function GitProviderDropdown({
  items,
  onSelectionChange,
  onInputChange,
  defaultFilter,
}: GitProviderDropdownProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="git-provider-dropdown"
      name="git-provider-dropdown"
      placeholder={t(I18nKey.COMMON$SELECT_GIT_PROVIDER)}
      items={items}
      wrapperClassName="max-w-[500px]"
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
      defaultFilter={defaultFilter}
    />
  );
}
