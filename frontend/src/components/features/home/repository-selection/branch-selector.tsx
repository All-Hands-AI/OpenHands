import React from "react";
import { Branch, GitRepository } from "#/types/git";
import { RepositoryLoadingState } from "./repository-loading-state";
import { RepositoryErrorState } from "./repository-error-state";
import { BranchDropdown } from "./branch-dropdown";
import { BranchLoadingState } from "./branch-loading-state";
import { BranchErrorState } from "./branch-error-state";

interface BranchSelectorProps {
  selectedRepository: GitRepository | null;
  selectedBranch: Branch | null;
  branches: Branch[] | undefined;
  onBranchChange: (branch: Branch | null) => void;
  isLoadingRepositories: boolean;
  isRepositoriesError: boolean;
  isLoadingBranches: boolean;
  isBranchesError: boolean;
}

export function BranchSelector({
  selectedRepository,
  selectedBranch,
  branches,
  onBranchChange,
  isLoadingRepositories,
  isRepositoriesError,
  isLoadingBranches,
  isBranchesError,
}: BranchSelectorProps) {
  const handleBranchSelection = (key: React.Key | null) => {
    const selectedBranchObj = branches?.find((branch) => branch.name === key);
    onBranchChange(selectedBranchObj || null);
  };

  const handleBranchInputChange = (value: string) => {
    // Clear the selected branch if the input is empty or contains only whitespace
    // This fixes the issue where users can't delete the entire default branch name
    if (value === "" || value.trim() === "") {
      onBranchChange(null);
    }
  };

  if (isLoadingRepositories) {
    return <RepositoryLoadingState wrapperClassName="max-w-auto" />;
  }

  if (isRepositoriesError) {
    return <RepositoryErrorState wrapperClassName="max-w-auto" />;
  }

  if (!selectedRepository) {
    return (
      <BranchDropdown
        items={[]}
        onSelectionChange={() => {}}
        onInputChange={() => {}}
        isDisabled
        wrapperClassName="max-w-auto"
      />
    );
  }

  if (isLoadingBranches) {
    return <BranchLoadingState wrapperClassName="max-w-auto" />;
  }

  if (isBranchesError) {
    return <BranchErrorState wrapperClassName="max-w-auto" />;
  }

  const branchesItems = branches?.map((branch) => ({
    key: branch.name,
    label: branch.name,
  }));

  return (
    <BranchDropdown
      items={branchesItems || []}
      onSelectionChange={handleBranchSelection}
      onInputChange={handleBranchInputChange}
      isDisabled={false}
      selectedKey={selectedBranch?.name}
      wrapperClassName="max-w-auto"
    />
  );
}
