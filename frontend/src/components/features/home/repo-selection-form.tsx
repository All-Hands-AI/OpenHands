import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useRepositoryBranches } from "#/hooks/query/use-repository-branches";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { useUserProviders } from "#/hooks/use-user-providers";
import { Provider } from "#/types/settings";
import { GitProviderDropdown } from "../../common/git-provider-dropdown";
import { GitRepositoryDropdown } from "../../common/git-repository-dropdown";
import { GitBranchDropdown } from "../../common/git-branch-dropdown";
import { I18nKey } from "#/i18n/declaration";
import RepoForkedIcon from "#/icons/repo-forked.svg?react";
import {
  providerDropdownStyles,
  repoBranchDropdownStyles,
} from "#/components/common/react-select-styles";

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
  const [selectedProvider, setSelectedProvider] =
    React.useState<Provider | null>(null);

  const { providers } = useUserProviders();

  const { data: branches, isLoading: isLoadingBranches } =
    useRepositoryBranches(selectedRepository?.full_name || null);

  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();

  const isCreatingConversationElsewhere = useIsCreatingConversation();

  const { t } = useTranslation();

  // Auto-select provider if there's only one
  React.useEffect(() => {
    if (providers.length === 1 && !selectedProvider) {
      setSelectedProvider(providers[0]);
    }
  }, [providers, selectedProvider]);

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  // Check if repository has no branches (empty array after loading completes)
  const hasNoBranches = !isLoadingBranches && branches && branches.length === 0;

  const handleProviderSelection = (provider: Provider | null) => {
    if (provider === selectedProvider) {
      return;
    }

    setSelectedProvider(provider);
    setSelectedRepository(null); // Reset repository selection when provider changes
    setSelectedBranch(null); // Reset branch selection when provider changes
    onRepoSelection(null); // Reset parent component's selected repo
  };

  const handleBranchSelection = (branchName: string | null) => {
    const selectedBranchObj = branches?.find(
      (branch) => branch.name === branchName,
    );
    if (selectedBranchObj) {
      setSelectedBranch(selectedBranchObj);
    }
  };

  // Render the provider dropdown
  const renderProviderSelector = () => (
    <GitProviderDropdown
      providers={providers}
      value={selectedProvider}
      placeholder="Select Provider"
      className="max-w-[124px]"
      onChange={handleProviderSelection}
      styles={providerDropdownStyles}
      classNamePrefix="provider-dropdown"
    />
  );

  // Effect to auto-select main/master branch when branches are loaded
  React.useEffect(() => {
    if (branches?.length) {
      // Look for main or master branch
      const defaultBranch = branches.find(
        (branch) => branch.name === "main" || branch.name === "master",
      );

      // If found, select it, otherwise select the first branch
      setSelectedBranch(defaultBranch || branches[0]);
    }
  }, [branches]);

  // Render the repository selector using our new component
  const renderRepositorySelector = () => {
    const handleRepoSelection = (repository?: GitRepository) => {
      if (repository) {
        onRepoSelection(repository);
        setSelectedRepository(repository);
      } else {
        setSelectedRepository(null);
        setSelectedBranch(null);
      }
    };

    return (
      <GitRepositoryDropdown
        provider={selectedProvider || providers[0]}
        value={selectedRepository?.id || null}
        placeholder="Search repositories..."
        disabled={!selectedProvider}
        onChange={handleRepoSelection}
        className="max-w-auto"
        styles={repoBranchDropdownStyles}
        classNamePrefix="repo-branch-dropdown"
      />
    );
  };

  // Render the branch selector
  const renderBranchSelector = () => (
    <GitBranchDropdown
      testId="branch-dropdown"
      repositoryName={selectedRepository?.full_name}
      value={selectedBranch?.name || null}
      placeholder="Select branch..."
      className="max-w-[500px]"
      disabled={!selectedRepository}
      onChange={handleBranchSelection}
      styles={repoBranchDropdownStyles}
      classNamePrefix="repo-branch-dropdown"
    />
  );

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

      <div className="flex items-center justify-between">
        <span className="text-sm text-white font-normal leading-5">
          {t(I18nKey.HOME$SELECT_OR_INSERT_URL)}
        </span>
        {renderProviderSelector()}
      </div>
      {renderRepositorySelector()}
      {renderBranchSelector()}

      <BrandButton
        testId="repo-launch-button"
        variant="primary"
        type="button"
        isDisabled={
          !selectedRepository ||
          (!selectedBranch && !hasNoBranches) ||
          isLoadingBranches ||
          isCreatingConversation ||
          (providers.length > 1 && !selectedProvider)
        }
        onClick={() =>
          createConversation(
            {
              repository: {
                name: selectedRepository?.full_name || "",
                gitProvider: selectedRepository?.git_provider || "github",
                branch: selectedBranch?.name || (hasNoBranches ? "" : "main"),
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
