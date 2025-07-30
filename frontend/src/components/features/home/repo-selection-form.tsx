import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useRepositoryBranches } from "#/hooks/query/use-repository-branches";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useDebounce } from "#/hooks/use-debounce";
import {
  GitProviderSelector,
  RepositorySelector,
  BranchSelector,
} from "./repository-selection";
import RepoForkedIcon from "#/icons/repo-forked.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { IOption } from "#/api/open-hands.types";

interface RepositorySelectionFormProps {
  onRepoSelection: (repo: GitRepository | null) => void;
}

export function RepositorySelectionForm({
  onRepoSelection,
}: RepositorySelectionFormProps) {
  const navigate = useNavigate();
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const [selectedBranch, setSelectedBranch] = React.useState<Branch | null>(
    null,
  );
  const [selectedGitProvider, setSelectedGitProvider] =
    React.useState<IOption<string> | null>(null);
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

  const handleGitProviderChange = (provider: IOption<string> | null) => {
    setSelectedGitProvider(provider);
    // Clear repository and branch selection when git provider changes
    onRepoSelection(null);
    setSelectedRepository(null);
    setSelectedBranch(null);
    branchManuallyClearedRef.current = false;
  };

  const handleRepositoryChange = (repo: GitRepository | null) => {
    setSelectedRepository(repo);
    onRepoSelection(repo);
    setSelectedBranch(null); // Reset branch selection when repo changes
    branchManuallyClearedRef.current = false; // Reset the flag when repo changes
  };

  const handleBranchChange = (branch: Branch | null) => {
    setSelectedBranch(branch);
    // Reset the manually cleared flag when a branch is explicitly selected
    branchManuallyClearedRef.current = false;
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-[10px]">
          <RepoForkedIcon width={24} height={24} />
          <span className="leading-5 font-bold text-base text-white">
            {t(I18nKey.COMMON$OPEN_REPOSITORY)}
          </span>
        </div>
      </div>

      <GitProviderSelector
        selectedGitProvider={selectedGitProvider}
        onGitProviderChange={handleGitProviderChange}
        isLoadingRepositories={isLoadingRepositories}
        isRepositoriesError={isRepositoriesError}
      />

      <RepositorySelector
        selectedGitProvider={selectedGitProvider}
        allRepositories={allRepositories}
        onRepositoryChange={handleRepositoryChange}
        onSearchQueryChange={setSearchQuery}
        isLoadingRepositories={isLoadingRepositories}
        isRepositoriesError={isRepositoriesError}
      />

      <BranchSelector
        selectedRepository={selectedRepository}
        selectedBranch={selectedBranch}
        branches={branches}
        onBranchChange={handleBranchChange}
        isLoadingRepositories={isLoadingRepositories}
        isRepositoriesError={isRepositoriesError}
        isLoadingBranches={isLoadingBranches}
        isBranchesError={isBranchesError}
      />

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
          createConversation(
            {
              repository: {
                name: selectedRepository?.full_name || "",
                gitProvider: selectedRepository?.git_provider || "github",
                branch: selectedBranch?.name || "main",
              },
            },
            {
              onSuccess: (data) =>
                navigate(`/conversations/${data.conversation_id}`),
            },
          )
        }
        className="w-full font-semibold"
      >
        {!isCreatingConversation && "Launch"}
        {isCreatingConversation && t("HOME$LOADING")}
      </BrandButton>
    </div>
  );
}
