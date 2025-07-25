import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useRepositoryBranches } from "#/hooks/query/use-repository-branches";
import { useGitRepositories } from "#/hooks/query/use-git-repositories";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { useUserProviders } from "#/hooks/use-user-providers";
import { Provider } from "#/types/settings";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { GitRepositoryAutocomplete } from "../../common/git-repository-autocomplete";
import { BranchDropdown } from "./repository-selection";

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
  const { data: repositoriesData, isError: isRepositoriesError } =
    useGitRepositories({
      provider: selectedProvider || providers[0],
      enabled: !!selectedProvider,
    });

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

  // Create provider dropdown items
  const providerItems = React.useMemo(
    () =>
      providers.map((provider) => ({
        key: provider,
        label: provider.charAt(0).toUpperCase() + provider.slice(1), // Capitalize first letter
      })),
    [providers],
  );

  const handleProviderSelection = (key: React.Key | null) => {
    const provider = key as Provider | null;
    setSelectedProvider(provider);
    setSelectedRepository(null); // Reset repository selection when provider changes
    setSelectedBranch(null); // Reset branch selection when provider changes
    onRepoSelection(null); // Reset parent component's selected repo
  };

  const handleBranchSelection = (key: React.Key | null) => {
    const selectedBranchObj = branches?.find((branch) => branch.name === key);
    setSelectedBranch(selectedBranchObj || null);
    // Reset the manually cleared flag when a branch is explicitly selected
    branchManuallyClearedRef.current = false;
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

  // Render the provider dropdown
  const renderProviderSelector = () => {
    // Only render if there are multiple providers
    if (providers.length <= 1) {
      return null;
    }

    return (
      <SettingsDropdownInput
        testId="provider-dropdown"
        name="provider-dropdown"
        placeholder="Select Provider"
        items={providerItems}
        wrapperClassName="max-w-[500px]"
        onSelectionChange={handleProviderSelection}
        selectedKey={selectedProvider || undefined}
      />
    );
  };

  // Extract repositories from paginated data structure
  const repositories = React.useMemo(() => {
    if (!repositoriesData?.pages) return [];
    return repositoriesData.pages.flatMap((page) => page.data);
  }, [repositoriesData]);

  // Render the repository selector using our new component
  const renderRepositorySelector = () => {
    const handleRepoSelection = (key: React.Key | null) => {
      const repoId = key?.toString();
      const selectedRepo = repositories.find((repo) => repo.id === repoId);
      if (selectedRepo) onRepoSelection(selectedRepo);
      setSelectedRepository(selectedRepo || null);
      setSelectedBranch(null); // Reset branch selection when repo changes
      branchManuallyClearedRef.current = false; // Reset the flag when repo changes
    };

    return (
      <GitRepositoryAutocomplete
        provider={selectedProvider || providers[0]}
        placeholder={
          selectedProvider
            ? "Search repositories..."
            : "Please select a provider first"
        }
        disabled={!selectedProvider}
        onSelectionChange={handleRepoSelection}
        errorMessage={
          isRepositoriesError ? "Failed to load repositories" : undefined
        }
        className="max-w-[500px]"
      />
    );
  };

  // Render the branch selector
  const renderBranchSelector = () => {
    const branchesItems =
      branches?.map((branch) => ({
        key: branch.name,
        label: branch.name,
      })) || [];

    return (
      <BranchDropdown
        items={branchesItems}
        onSelectionChange={handleBranchSelection}
        onInputChange={handleBranchInputChange}
        isDisabled={!selectedRepository || isLoadingBranches}
        selectedKey={selectedBranch?.name}
      />
    );
  };

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
          isRepositoriesError ||
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
