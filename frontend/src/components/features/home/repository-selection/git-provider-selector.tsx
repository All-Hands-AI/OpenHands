import React from "react";
import { GIT_PROVIDER_OPTIONS } from "#/utils/constants";
import { IOption } from "#/api/open-hands.types";
import { GitProviderDropdown } from "./git-provider-dropdown";
import { RepositoryLoadingState } from "./repository-loading-state";
import { RepositoryErrorState } from "./repository-error-state";

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

  if (isLoadingRepositories) {
    return <RepositoryLoadingState wrapperClassName="max-w-auto" />;
  }

  if (isRepositoriesError) {
    return <RepositoryErrorState wrapperClassName="max-w-auto" />;
  }

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
      wrapperClassName="max-w-auto"
    />
  );
}
