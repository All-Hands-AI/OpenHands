import React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { useSearchRepositories } from "#/hooks/query/use-search-repositories";
import { useDebounce } from "#/hooks/use-debounce";
import { sanitizeQuery } from "#/utils/sanitize-query";

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
  defaultFilter?: (textValue: string, inputValue: string) => boolean;
}

function RepositoryDropdown({
  items,
  onSelectionChange,
  onInputChange,
  defaultFilter,
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
      defaultFilter={defaultFilter}
    />
  );
}

export function RepositorySelectionForm({
  onRepoSelection,
}: RepositorySelectionFormProps) {
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const {
    data: repositories,
    isLoading: isLoadingRepositories,
    isError: isRepositoriesError,
  } = useUserRepositories();
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

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  const allRepositories = repositories?.concat(searchedRepos || []);
  const repositoriesItems = allRepositories?.map((repo) => ({
    key: repo.id,
    label: repo.full_name,
  }));

  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = allRepositories?.find(
      (repo) => repo.id.toString() === key,
    );

    if (selectedRepo) onRepoSelection(selectedRepo.full_name);
    setSelectedRepository(selectedRepo || null);
  };

  const handleInputChange = (value: string) => {
    if (value === "") {
      setSelectedRepository(null);
      onRepoSelection(null);
    } else if (value.startsWith("https://github.com/")) {
      const repoName = sanitizeQuery(value);
      setSearchQuery(repoName);
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
        onInputChange={handleInputChange}
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

  return (
    <>
      {renderRepositorySelector()}

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
          })
        }
      >
        {!isCreatingConversation && "Launch"}
        {isCreatingConversation && t("HOME$LOADING")}
      </BrandButton>
    </>
  );
}
