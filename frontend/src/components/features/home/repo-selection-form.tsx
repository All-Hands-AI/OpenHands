import React from "react";
import { useTranslation } from "react-i18next";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { GitRepository } from "#/types/git";
import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";

interface RepositorySelectionFormProps {
  onRepoSelection: (repoTitle: string | null) => void;
}

export function RepositorySelectionForm({
  onRepoSelection,
}: RepositorySelectionFormProps) {
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const { data: repositories } = useUserRepositories();
  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();
  const isCreatingConversationElsewhere = useIsCreatingConversation();
  const { t } = useTranslation();

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  const repositoriesList = repositories?.pages.flatMap((page) => page.data);
  const repositoriesItems = repositoriesList?.map((repo) => ({
    key: repo.id,
    label: repo.full_name,
  }));

  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = repositoriesList?.find(
      (repo) => repo.id.toString() === key,
    );

    if (selectedRepo) onRepoSelection(selectedRepo.full_name);
    setSelectedRepository(selectedRepo || null);
  };

  const handleInputChange = (value: string) => {
    if (value === "") {
      setSelectedRepository(null);
      onRepoSelection(null);
    }
  };

  return (
    <>
      <SettingsDropdownInput
        testId="repo-dropdown"
        name="repo-dropdown"
        placeholder="Select a repo"
        items={repositoriesItems || []}
        wrapperClassName="max-w-[500px]"
        onSelectionChange={handleRepoSelection}
        onInputChange={handleInputChange}
      />

      <BrandButton
        testId="repo-launch-button"
        variant="primary"
        type="button"
        isDisabled={!selectedRepository || isCreatingConversation}
        onClick={() => createConversation({ selectedRepository })}
      >
        {!isCreatingConversation && "Launch"}
        {isCreatingConversation && t("HOME$LOADING")}
      </BrandButton>
    </>
  );
}
