import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import React from "react";
import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { useConfig } from "#/hooks/query/use-config";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { GitRepository } from "#/types/git";

interface RepoConnectorProps {
  onRepoSelection?: (repoTitle: string) => void;
}

export function RepoConnector({ onRepoSelection }: RepoConnectorProps) {
  const [selectedRepository, setSelectedRepository] =
    React.useState<GitRepository | null>(null);
  const { data: config } = useConfig();
  const { data: repositories } = useUserRepositories();
  const { mutate: createConversation } = useCreateConversation();

  const isOSS = config?.APP_MODE === "oss";
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
      />

      <BrandButton
        testId="launch-button"
        variant="primary"
        type="button"
        isDisabled={!selectedRepository}
        onClick={() => createConversation({ selectedRepository })}
      >
        Launch
      </BrandButton>

      {isOSS && (
        <div className="flex flex-col text-sm underline underline-offset-2 text-content-2 gap-4 w-fit">
          <a href="http://" target="_blank" rel="noopener noreferrer">
            Add GitHub repos
          </a>
          <a href="http://" target="_blank" rel="noopener noreferrer">
            Add GitLab repos
          </a>
        </div>
      )}
    </section>
  );
}
