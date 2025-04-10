import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import React from "react";
import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";
import { useConfig } from "#/hooks/query/use-config";

export function RepoConnector() {
  const [repoIsSelected, setRepoIsSelected] = React.useState(false);
  const { data: config } = useConfig();
  const { data: repositories } = useUserRepositories();

  const isOSS = config?.APP_MODE === "oss";
  const repositoriesList = repositories?.pages.flatMap((page) => page.data);
  const repositoriesItems = repositoriesList?.map((repo) => ({
    key: repo.id,
    label: repo.full_name,
  }));

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
        onSelectionChange={(key) => {
          setRepoIsSelected(!!key);
        }}
      />

      <BrandButton
        testId="launch-button"
        variant="primary"
        type="button"
        isDisabled={!repoIsSelected}
      >
        Launch
      </BrandButton>

      {isOSS && (
        <div className="flex flex-col text-sm underline underline-offset-2 text-content-2 gap-4">
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
