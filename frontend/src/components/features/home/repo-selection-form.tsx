import React from "react";
import { useTranslation } from "react-i18next";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useRepositoryBranches } from "#/hooks/query/use-repository-branches";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useDebounce } from "#/hooks/use-debounce";
import { sanitizeQuery } from "#/utils/sanitize-query";
import {
  RepositoryDropdown,
  RepositoryLoadingState,
  RepositoryErrorState,
  BranchDropdown,
  BranchLoadingState,
  BranchErrorState,
} from "./repository-selection";

interface RepositorySelectionFormProps {
  onRepoSelection: (repoTitle: string | null) => void;
}

export function RepositorySelectionForm({
  onRepoSelection,
}: RepositorySelectionFormProps) {
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const [selectedBranch, setSelectedBranch] = React.useState<Branch | null>(
    null,
  );
  // Add a ref to track if the branch was manually cleared by the user
  const branchManuallyClearedRef = React.useRef<boolean>(false);
  const {
    data: repositories,
    isLoading: isLoadingRepositories,
    isError: isRepositoriesError,
  } = useUserRepositories();
  const {
    data: branches,
    isLoading: isLoadingBranches,
    isError: isBranchesError,
  } = useRepositoryBranches(selectedRepository?.full_name || null);
  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();
  const isCreatingConversationElsewhere = useIsCreatingConversation();
  const { t } = useTranslation();

  const [searchQuery, setSearchQuery] = React.useState("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const { data: searchedRepos } = useSearchRepositories(debouncedSearchQuery);

  // Auto-select main or master branch if it exists, but only if the branch wasn't manually cleared
  React.useEffect(() => {
    if (
      branches &&
      branches.length > 0 &&
      !selectedBranch &&
      !isLoadingBranches &&
      !branchManuallyClearedRef.current // Only auto-select if not manually cleared
    ) {
      // Look for main or master branch
      const mainBranch = branches.find((branch) => branch.name === "main");
      const masterBranch = branches.find((branch) => branch.name === "master");

      // Select main if it exists, otherwise select master if it exists
      if (mainBranch) {
        setSelectedBranch(mainBranch);
      } else if (masterBranch) {
        setSelectedBranch(masterBranch);
      }
    }
  }, [branches, isLoadingBranches, selectedBranch]);

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  const allRepositories = repositories?.concat(searchedRepos || []);
  const repositoriesItems = allRepositories?.map((repo) => ({
    key: repo.id,
    label: decodeURIComponent(repo.full_name),
  }));

  const branchesItems = branches?.map((branch) => ({
    key: branch.name,
    label: branch.name,
  }));

  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = allRepositories?.find((repo) => repo.id === key);

    if (selectedRepo) onRepoSelection(selectedRepo.full_name);
    setSelectedRepository(selectedRepo || null);
    setSelectedBranch(null); // Reset branch selection when repo changes
    branchManuallyClearedRef.current = false; // Reset the flag when repo changes
  };

  const handleBranchSelection = (key: React.Key | null) => {
    const selectedBranchObj = branches?.find((branch) => branch.name === key);
    setSelectedBranch(selectedBranchObj || null);
    // Reset the manually cleared flag when a branch is explicitly selected
    branchManuallyClearedRef.current = false;
  };

  const handleRepoInputChange = (value: string) => {
    if (value === "") {
      setSelectedRepository(null);
      setSelectedBranch(null);
      onRepoSelection(null);
    } else if (value.startsWith("https://")) {
      const repoName = sanitizeQuery(value);
      setSearchQuery(repoName);
    }
  };

  const handleBranchInputChange = (value: string) => {
    // Clear the selected branch if the input is empty or contains only whitespace
    // This fixes the issue where users can't delete the entire default branch name
    if (value === "" || value.trim() === "") {
      setSelectedBranch(null);
      // Set the flag to indicate that the branch was manually cleared
      branchManuallyClearedRef.current = true;
    } else {
      // Reset the flag when the user starts typing again
      branchManuallyClearedRef.current = false;
    }
  };

  // Render the appropriate UI based on the loading/error state
  const renderRepositorySelector = () => {
    if (isLoadingRepositories) {
      return <RepositoryLoadingState />;
    }

    if (isRepositoriesError) {
      return <RepositoryErrorState />;
    }

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
      />
    );
  };

  // Render the appropriate UI for branch selector based on the loading/error state
  const renderBranchSelector = () => {
    if (!selectedRepository) {
      return (
        <BranchDropdown
          items={[]}
          onSelectionChange={() => {}}
          onInputChange={() => {}}
          isDisabled
        />
      );
    }

    if (isLoadingBranches) {
      return <BranchLoadingState />;
    }

    if (isBranchesError) {
      return <BranchErrorState />;
    }

    return (
      <BranchDropdown
        items={branchesItems || []}
        onSelectionChange={handleBranchSelection}
        onInputChange={handleBranchInputChange}
        isDisabled={false}
        selectedKey={selectedBranch?.name}
      />
    );
  };

  return (
    <div className="flex flex-col gap-4">
      {renderRepositorySelector()}

      {renderBranchSelector()}

      <BrandButton
        testId="repo-launch-button"
        variant="primary"
        type="button"
        isDisabled={
          !selectedRepository ||
          isCreatingConversation ||
          isLoadingRepositories ||
          isRepositoriesError
        }
        onClick={() =>
          createConversation({
            selectedRepository,
            selected_branch: selectedBranch?.name,
          })
        }
      >
        {!isCreatingConversation && "Launch"}
        {isCreatingConversation && t("HOME$LOADING")}
      </BrandButton>
    </div>
  );
}
