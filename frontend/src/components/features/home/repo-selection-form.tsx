import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
// Removed useRepositoryBranches import - GitBranchDropdown manages its own data
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { useUserProviders } from "#/hooks/use-user-providers";
import { Provider } from "#/types/settings";
import { GitProviderDropdown } from "../../common/git-provider-dropdown";
import { GitRepositoryDropdown } from "../../common/git-repository-dropdown";
import { GitBranchDropdown } from "../../common/git-branch-dropdown";

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

  // Branch selection is now handled by GitBranchDropdown component

  const handleProviderSelection = (provider: Provider | null) => {
    setSelectedProvider(provider);
    setSelectedRepository(null); // Reset repository selection when provider changes
    setSelectedBranch(null); // Reset branch selection when provider changes
    onRepoSelection(null); // Reset parent component's selected repo
  };

  const handleBranchSelection = (branchName: string | null) => {
    if (branchName) {
      // Create a simple Branch object since we only need the name
      setSelectedBranch({ name: branchName } as Branch);
    } else {
      setSelectedBranch(null);
    }
  };

  // Render the provider dropdown
  const renderProviderSelector = () => {
    // Only render if there are multiple providers
    if (providers.length <= 1) {
      return null;
    }

    return (
      <GitProviderDropdown
        providers={providers}
        value={selectedProvider}
        placeholder="Select Provider"
        className="max-w-[500px]"
        onChange={handleProviderSelection}
      />
    );
  };

  // Reset branch selection when repository changes
  React.useEffect(() => {
    // Always reset branch selection when repository changes
    // The GitBranchDropdown will auto-select the default branch once branches are loaded
    setSelectedBranch(null);
  }, [selectedRepository]);

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
        className="max-w-[500px]"
      />
    );
  };

  // Render the branch selector
  const renderBranchSelector = () => (
    <GitBranchDropdown
      repositoryName={selectedRepository?.full_name}
      defaultBranch={selectedRepository?.main_branch}
      value={selectedBranch?.name || null}
      placeholder="Select branch..."
      className="max-w-[500px]"
      disabled={!selectedRepository}
      onChange={handleBranchSelection}
    />
  );

  return (
    <div className="flex flex-col gap-4">
      {renderProviderSelector()}
      {renderRepositorySelector()}
      {renderBranchSelector()}

      <BrandButton
        testId="repo-launch-button"
        variant="primary"
        type="button"
        isDisabled={
          !selectedRepository ||
          !selectedBranch ||
          isCreatingConversation ||
          (providers.length > 1 && !selectedProvider)
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
      >
        {!isCreatingConversation && "Launch"}
        {isCreatingConversation && t("HOME$LOADING")}
      </BrandButton>
    </div>
  );
}
