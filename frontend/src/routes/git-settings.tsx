import React from "react";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useLogout } from "#/hooks/mutation/use-logout";
import { GitHubTokenInput } from "#/components/features/settings/git-settings/github-token-input";
import { GitLabTokenInput } from "#/components/features/settings/git-settings/gitlab-token-input";
import { ConfigureGitHubRepositoriesAnchor } from "#/components/features/settings/git-settings/configure-github-repositories-anchor";

function GitSettingsScreen() {
  const { mutate: saveSettings } = useSaveSettings();
  const { mutate: disconnectGitTokens } = useLogout();

  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  const [githubTokenInputHasValue, setGithubTokenInputHasValue] =
    React.useState(false);
  const [gitlabTokenInputHasValue, setGitlabTokenInputHasValue] =
    React.useState(false);

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = !!settings?.PROVIDER_TOKENS_SET.github;
  const isGitLabTokenSet = !!settings?.PROVIDER_TOKENS_SET.gitlab;

  const formAction = async (formData: FormData) => {
    const disconnectButtonClicked =
      formData.get("disconnect-tokens-button") !== null;

    if (disconnectButtonClicked) {
      disconnectGitTokens();
      return;
    }

    const githubToken = formData.get("github-token-input")?.toString() || "";
    const gitlabToken = formData.get("gitlab-token-input")?.toString() || "";

    saveSettings({
      provider_tokens: {
        github: githubToken,
        gitlab: gitlabToken,
      },
    });
  };

  return (
    <form
      data-testid="git-settings-screen"
      action={formAction}
      className="flex flex-col h-full justify-between"
    >
      {isSaas && config.APP_SLUG && (
        <ConfigureGitHubRepositoriesAnchor slug={config.APP_SLUG} />
      )}

      {!isSaas && (
        <div className="px-11 py-9 flex flex-col gap-12">
          <GitHubTokenInput
            name="github-token-input"
            isGitHubTokenSet={isGitHubTokenSet}
            onChange={(value) => {
              setGithubTokenInputHasValue(!!value);
            }}
          />

          <GitLabTokenInput
            name="gitlab-token-input"
            isGitLabTokenSet={isGitLabTokenSet}
            onChange={(value) => {
              setGitlabTokenInputHasValue(!!value);
            }}
          />
        </div>
      )}

      <div className="flex gap-6 p-6 justify-end border-t border-t-tertiary">
        <BrandButton
          testId="disconnect-tokens-button"
          name="disconnect-tokens-button"
          type="submit"
          variant="secondary"
          isDisabled={!isGitHubTokenSet && !isGitLabTokenSet}
        >
          Disconnect Tokens
        </BrandButton>

        <BrandButton
          testId="submit-button"
          type="submit"
          variant="primary"
          isDisabled={!githubTokenInputHasValue && !gitlabTokenInputHasValue}
        >
          Save Changes
        </BrandButton>
      </div>
    </form>
  );
}

export default GitSettingsScreen;
