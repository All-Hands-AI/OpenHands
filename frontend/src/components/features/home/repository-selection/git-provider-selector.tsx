import React from "react";
import { GIT_PROVIDER_OPTIONS } from "#/utils/constants";
import { IOption } from "#/api/open-hands.types";
import { GitProviderDropdown } from "./git-provider-dropdown";

interface GitProviderSelectorProps {
  selectedGitProvider: IOption<string> | null;
  onGitProviderChange: (provider: IOption<string> | null) => void;
  isLoadingRepositories: boolean;
  isRepositoriesError: boolean;
}

export function GitProviderSelector({
  selectedGitProvider,
  onGitProviderChange,
  isLoadingRepositories,
  isRepositoriesError,
}: GitProviderSelectorProps) {
  const handleGitProviderSelection = (key: React.Key | null) => {
    const currentGitProvider = GIT_PROVIDER_OPTIONS.find(
      (provider) => provider.value === key,
    );
    onGitProviderChange(currentGitProvider || null);
  };

  const handleGitProviderInputChange = (value: string) => {
    if (value === "") {
      onGitProviderChange(null);
    }
  };

  return (
    <GitProviderDropdown
      items={GIT_PROVIDER_OPTIONS.map((provider) => ({
        key: provider.value,
        label: provider.label,
      }))}
      onSelectionChange={handleGitProviderSelection}
      onInputChange={handleGitProviderInputChange}
      defaultFilter={(textValue, inputValue) => {
        if (!inputValue) return true;

        const gitProvider = GIT_PROVIDER_OPTIONS.find(
          (provider) => provider.label === textValue,
        );

        return !!gitProvider;
      }}
      selectedKey={selectedGitProvider?.value}
      wrapperClassName="max-w-[124px]"
      inputWrapperClassName="h-6 min-h-6 max-h-6 py-0"
      inputClassName="text-xs font-normal leading-5 pr-0"
      isClearable={false}
      isDisabled={isLoadingRepositories || isRepositoriesError}
    />
  );
}
