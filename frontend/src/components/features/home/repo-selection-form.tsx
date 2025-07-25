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
  // Add a ref to track if the branch was manually cleared by the user
  const branchManuallyClearedRef = React.useRef<boolean>(false);
  const { providers } = useUserProviders();
  const { data: branches } = useRepositoryBranches(
    selectedRepository?.full_name || null,
  );
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

  const handleProviderSelection = (provider: Provider | null) => {
    setSelectedProvider(provider);
    setSelectedRepository(null); // Reset repository selection when provider changes
    setSelectedBranch(null); // Reset branch selection when provider changes
    onRepoSelection(null); // Reset parent component's selected repo
  };

  const handleBranchSelection = (branchName: string | null) => {
    const selectedBranchObj = branches?.find(
      (branch) => branch.name === branchName,
    );
    setSelectedBranch(selectedBranchObj || null);
    // Reset the manually cleared flag when a branch is explicitly selected
    branchManuallyClearedRef.current = false;
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

  // Render the repository selector using our new component
  const renderRepositorySelector = () => {
    const handleRepoSelection = (repository?: GitRepository) => {
      if (repository) onRepoSelection(repository);
      setSelectedRepository(repository || null);
      setSelectedBranch(null); // Reset branch selection when repo changes
      branchManuallyClearedRef.current = false; // Reset the flag when repo changes
    };

    return (
      <GitRepositoryDropdown
        provider={selectedProvider || providers[0]}
        value={selectedRepository?.id || null}
        placeholder={
          selectedProvider
            ? "Search repositories..."
            : "Please select a provider first"
        }
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
