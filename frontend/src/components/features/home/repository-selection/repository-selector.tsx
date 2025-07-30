import React from "react";
import { GitRepository } from "#/types/git";
import { sanitizeQuery } from "#/utils/sanitize-query";
import { IOption } from "#/api/open-hands.types";
import { RepositoryLoadingState } from "./repository-loading-state";
import { RepositoryErrorState } from "./repository-error-state";
import { RepositoryDropdown } from "./repository-dropdown";

interface RepositorySelectorProps {
  selectedGitProvider: IOption<string> | null;
  allRepositories: GitRepository[] | undefined;
  onRepositoryChange: (repo: GitRepository | null) => void;
  onSearchQueryChange?: (query: string) => void;
  isLoadingRepositories: boolean;
  isRepositoriesError: boolean;
}

export function RepositorySelector({
  selectedGitProvider,
  allRepositories,
  onRepositoryChange,
  onSearchQueryChange,
  isLoadingRepositories,
  isRepositoriesError,
}: RepositorySelectorProps) {
  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = allRepositories?.find((repo) => repo.id === key);
    onRepositoryChange(selectedRepo || null);
  };

  const handleRepoInputChange = (value: string) => {
    console.log("handleRepoInputChange", value);
    if (value === "") {
      onRepositoryChange(null);
      onSearchQueryChange?.("");
    } else if (value.startsWith("https://")) {
      const repoName = sanitizeQuery(value);
      onSearchQueryChange?.(repoName);
      onRepositoryChange(null);
    }
  };

  const getRepositoriesItems = () => {
    if (!allRepositories) {
      return [];
    }

    if (selectedGitProvider) {
      return allRepositories
        .filter((repo) => repo.git_provider === selectedGitProvider.value)
        .map((repo) => ({
          key: repo.id,
          label: decodeURIComponent(repo.full_name),
        }));
    }

    return allRepositories.map((repo) => ({
      key: repo.id,
      label: decodeURIComponent(repo.full_name),
    }));
  };

  if (isLoadingRepositories) {
    return <RepositoryLoadingState wrapperClassName="max-w-auto" />;
  }

  if (isRepositoriesError) {
    return <RepositoryErrorState wrapperClassName="max-w-auto" />;
  }

  const repositoriesItems = getRepositoriesItems();

  return (
    <RepositoryDropdown
      items={repositoriesItems || []}
      onSelectionChange={handleRepoSelection}
      onInputChange={handleRepoInputChange}
      defaultFilter={(textValue, inputValue) => {
        if (!inputValue) return true;

        const repo = allRepositories?.find((r) => r.full_name === textValue);
        if (!repo) return false;

        const sanitizedInput = sanitizeQuery(inputValue);
        return sanitizeQuery(textValue).includes(sanitizedInput);
      }}
      wrapperClassName="max-w-auto"
    />
  );
}
