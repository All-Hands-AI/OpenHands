import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsDropdownInput } from "../../settings/settings-dropdown-input";
import { I18nKey } from "#/i18n/declaration";
import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import { Provider } from "#/types/settings";
import { cn } from "#/utils/utils";

export interface GitProviderDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
  defaultFilter?: (textValue: string, inputValue: string) => boolean;
  selectedKey?: string;
  wrapperClassName?: string;
}

export function GitProviderDropdown({
  items,
  onSelectionChange,
  onInputChange,
  defaultFilter,
  selectedKey,
  wrapperClassName,
}: GitProviderDropdownProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="git-provider-dropdown"
      name="git-provider-dropdown"
      placeholder={t(I18nKey.COMMON$SELECT_GIT_PROVIDER)}
      items={items}
      wrapperClassName={cn("max-w-[500px]", wrapperClassName)}
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
      defaultFilter={defaultFilter}
      startContent={
        selectedKey && (
          <GitProviderIcon
            gitProvider={selectedKey as Provider}
            className="w-[14px] h-[14px]"
          />
        )
      }
    />
  );
}
