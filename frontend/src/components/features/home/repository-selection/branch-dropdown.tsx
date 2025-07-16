import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../../settings/settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";

export interface BranchDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
  isDisabled: boolean;
  selectedKey?: string;
}

export function BranchDropdown({
  items,
  onSelectionChange,
  onInputChange,
  isDisabled,
  selectedKey,
}: BranchDropdownProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="branch-dropdown"
      name="branch-dropdown"
      placeholder={t(I18nKey.REPOSITORY$SELECT_BRANCH)}
      items={items}
      wrapperClassName="max-w-[500px]"
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
      isDisabled={isDisabled}
      selectedKey={selectedKey}
    />
  );
}
