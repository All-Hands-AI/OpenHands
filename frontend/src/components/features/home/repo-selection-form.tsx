import React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useRepositoryBranches } from "#/hooks/query/use-repository-branches";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";

interface RepositorySelectionFormProps {
  onRepoSelection: (repoTitle: string | null) => void;
}

// Loading state component
function RepositoryLoadingState() {
  const { t } = useTranslation();
  return (
    <div
      data-testid="repo-dropdown-loading"
      className="flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded"
    >
      <Spinner size="sm" />
      <span className="text-sm">{t("HOME$LOADING_REPOSITORIES")}</span>
    </div>
  );
}

// Error state component
function RepositoryErrorState() {
  const { t } = useTranslation();
  return (
    <div
      data-testid="repo-dropdown-error"
      className="flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded text-red-500"
    >
      <span className="text-sm">{t("HOME$FAILED_TO_LOAD_REPOSITORIES")}</span>
    </div>
  );
}

// Repository dropdown component
interface RepositoryDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
}

function RepositoryDropdown({
  items,
  onSelectionChange,
  onInputChange,
}: RepositoryDropdownProps) {
  return (
    <SettingsDropdownInput
      testId="repo-dropdown"
      name="repo-dropdown"
      placeholder="Select a repo"
      items={items}
      wrapperClassName="max-w-[500px]"
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
    />
  );
}

// Branch loading state component
function BranchLoadingState() {
  const { t } = useTranslation();
  return (
    <div
      data-testid="branch-dropdown-loading"
      className="flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded"
    >
      <Spinner size="sm" />
      <span className="text-sm">{t("HOME$LOADING_BRANCHES")}</span>
    </div>
  );
}

// Branch error state component
function BranchErrorState() {
  const { t } = useTranslation();
  return (
    <div
      data-testid="branch-dropdown-error"
      className="flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded text-red-500"
    >
      <span className="text-sm">{t("HOME$FAILED_TO_LOAD_BRANCHES")}</span>
    </div>
  );
}

// Branch dropdown component
interface BranchDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  onInputChange: (value: string) => void;
  isDisabled: boolean;
}

function BranchDropdown({
  items,
  onSelectionChange,
  onInputChange,
  isDisabled,
}: BranchDropdownProps) {
  return (
    <SettingsDropdownInput
      testId="branch-dropdown"
      name="branch-dropdown"
      placeholder="Select a branch"
      items={items}
      wrapperClassName="max-w-[500px]"
      onSelectionChange={onSelectionChange}
      onInputChange={onInputChange}
      isDisabled={isDisabled}
    />
  );
}

export function RepositorySelectionForm({
  onRepoSelection,
}: RepositorySelectionFormProps) {
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const [selectedBranch, setSelectedBranch] = React.useState<Branch | null>(
    null,
  );
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

  // Auto-select main or master branch if it exists
  React.useEffect(() => {
    if (
      branches &&
      branches.length > 0 &&
      !selectedBranch &&
      !isLoadingBranches
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
  }, [branches, selectedBranch, isLoadingBranches]);

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  const repositoriesItems = repositories?.map((repo) => ({
    key: repo.id,
    label: repo.full_name,
  }));

  const branchesItems = branches?.map((branch) => ({
    key: branch.name,
    label: branch.name,
  }));

  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = repositories?.find(
      (repo) => repo.id.toString() === key,
    );

    if (selectedRepo) onRepoSelection(selectedRepo.full_name);
    setSelectedRepository(selectedRepo || null);
    setSelectedBranch(null); // Reset branch selection when repo changes
  };

  const handleBranchSelection = (key: React.Key | null) => {
    const selectedBranchObj = branches?.find((branch) => branch.name === key);
    setSelectedBranch(selectedBranchObj || null);
  };

  const handleRepoInputChange = (value: string) => {
    if (value === "") {
      setSelectedRepository(null);
      setSelectedBranch(null);
      onRepoSelection(null);
    }
  };

  const handleBranchInputChange = (value: string) => {
    if (value === "") {
      setSelectedBranch(null);
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
            conversation_trigger: "gui",
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
