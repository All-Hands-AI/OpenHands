import React from "react";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { useConfig } from "#/hooks/query/use-config";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { GitRepository } from "#/types/git";
import { RepoProviderLinks } from "./repo-provider-links";

interface RepoConnectorProps {
  onRepoSelection?: (repoTitle: string | null) => void;
}

export function RepoConnector({ onRepoSelection }: RepoConnectorProps) {
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const { data: config } = useConfig();
  const { data: repositories } = useUserRepositories();
  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();

  // We check for isSuccess because the app might require time to render
  // into the new conversation screen after the conversation is created.
  const isCreatingConversation = isPending || isSuccess;

  const isSaaS = config?.APP_MODE === "saas";
  const repositoriesList = repositories?.pages.flatMap((page) => page.data);
  const repositoriesItems = repositoriesList?.map((repo) => ({
    key: repo.id,
    label: repo.full_name,
  }));

  const handleRepoSelection = (key: React.Key | null) => {
    const selectedRepo = repositoriesList?.find(
      (repo) => repo.id.toString() === key,
    );

    if (selectedRepo) onRepoSelection?.(selectedRepo.full_name);
    setSelectedRepository(selectedRepo || null);
  };

  const handleInputChange = (value: string) => {
    if (value === "") {
      setSelectedRepository(null);
      onRepoSelection?.(null);
    }
  };

  return (
    <section
      data-testid="repo-connector"
      className="w-full flex flex-col gap-6"
    >
      <h2 className="heading">Connect to a Repository</h2>

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
        testId="launch-button"
        variant="primary"
        type="button"
        isDisabled={!selectedRepository || isCreatingConversation}
        onClick={() => createConversation({ selectedRepository })}
      >
        {!isCreatingConversation && "Launch"}
        {isCreatingConversation && "Loading..."}
      </BrandButton>

      {isSaaS && <RepoProviderLinks />}
    </section>
  );
}
