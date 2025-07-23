import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useRepositories } from "#/hooks/query/use-repositories";
import { useRepositoryBranches } from "#/hooks/query/use-repository-branches";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { Branch, GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useDebounce } from "#/hooks/use-debounce";
import { useUserProviders } from "#/hooks/use-user-providers";
import { Provider } from "#/types/settings";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import {
  RepositoryDropdown,
  RepositoryLoadingState,
  RepositoryErrorState,
  BranchDropdown,
  BranchLoadingState,
  BranchErrorState,
} from "./repository-selection";

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
  const {
    data: repositoriesData,
    isLoading: isLoadingRepositories,
    isError: isRepositoriesError,
    hasNextPage,
    isFetchingNextPage,
    onLoadMore,
  } = useRepositories(selectedProvider);
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
  const { data: searchedRepos } = useSearchRepositories(
    debouncedSearchQuery,
    selectedProvider,
  );

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

  // Extract repositories from paginated data structure
  const repositories = React.useMemo(() => {
    if (!repositoriesData?.pages) return [];
    return repositoriesData.pages.flatMap((page) => page.data || []);
  }, [repositoriesData]);

  // Show search results when user is typing, otherwise show user repositories
  const allRepositories = React.useMemo(() => {
    if (searchQuery.trim()) {
      // User is typing - show only search results
      return searchedRepos || [];
    }
    // User is not typing - show user repositories
    return repositories || [];
  }, [repositories, searchedRepos, searchQuery]);

  const repositoriesItems = allRepositories.map((repo) => ({
    key: repo.id,
    label: decodeURIComponent(repo.full_name),
  }));

  const branchesItems = branches?.map((branch) => ({
    key: branch.name,
    label: branch.name,
  }));

  // Create provider dropdown items
  const providerItems = React.useMemo(
    () =>
      providers.map((provider) => ({
        key: provider,
        label: provider.charAt(0).toUpperCase() + provider.slice(1), // Capitalize first letter
      })),
    [providers],
  );

  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = allRepositories?.find((repo) => repo.id === key);
    if (selectedRepo) onRepoSelection(selectedRepo);
    setSelectedRepository(selectedRepo || null);
    setSelectedBranch(null); // Reset branch selection when repo changes
    branchManuallyClearedRef.current = false; // Reset the flag when repo changes
  };

  const handleProviderSelection = (key: React.Key | null) => {
    const provider = key as Provider | null;
    setSelectedProvider(provider);
    setSelectedRepository(null); // Reset repository selection when provider changes
    setSelectedBranch(null); // Reset branch selection when provider changes
    setSearchQuery(""); // Reset search query when provider changes
    onRepoSelection(null); // Reset parent component's selected repo
  };

  const handleBranchSelection = (key: React.Key | null) => {
    const selectedBranchObj = branches?.find((branch) => branch.name === key);
    setSelectedBranch(selectedBranchObj || null);
    // Reset the manually cleared flag when a branch is explicitly selected
    branchManuallyClearedRef.current = false;
  };

  const handleRepoInputChange = (value: string) => {
    // Always set the search query to exactly what the user types
    setSearchQuery(value);

    if (value === "") {
      setSelectedRepository(null);
      setSelectedBranch(null);
      onRepoSelection(null);
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

  // Render the appropriate UI based on the loading/error state
  const renderRepositorySelector = () => {
    // Disable repository selector if no provider is selected (and there are multiple providers)
    const isDisabled = providers.length > 1 && !selectedProvider;

    if (isDisabled) {
      return (
        <RepositoryDropdown
          items={[]}
          onSelectionChange={() => {}}
          onInputChange={() => {}}
          isDisabled
        />
      );
    }

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
        isDisabled={false}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        scrollRef={repositoriesData?.scrollRef}
        onOpenChange={repositoriesData?.onOpenChange}
        defaultFilter={(textValue, inputValue) => {
          if (!inputValue) return true;

          // When user is typing, show all search results (no additional filtering)
          if (searchQuery.trim()) {
            return true;
          }

          // When showing user repositories, filter by input
          return textValue.toLowerCase().includes(inputValue.toLowerCase());
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
          isLoadingRepositories ||
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
