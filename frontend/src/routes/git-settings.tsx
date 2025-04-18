import { useTranslation } from "react-i18next";
import React from "react";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { GitHubTokenHelpAnchor } from "#/components/features/settings/git-settings/github-token-help-anchor";
import { GitLabTokenHelpAnchor } from "#/components/features/settings/git-settings/gitlab-token-help-anchor";
import { useLogout } from "#/hooks/mutation/use-logout";

function GitSettingsScreen() {
  const { t } = useTranslation();

  const { mutate: saveSettings } = useSaveSettings();
  const { mutate: disconnectGitTokens } = useLogout();

  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  const [githubTokenInputHasValue, setGithubTokenInputHasValue] =
    React.useState(false);
  const [gitlabTokenInputHasValue, setGitlabTokenInputHasValue] =
    React.useState(false);

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = settings?.PROVIDER_TOKENS_SET.github;
  const isGitLabTokenSet = settings?.PROVIDER_TOKENS_SET.gitlab;

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
        <div data-testid="configure-github-repositories-button" />
      )}

      {!isSaas && (
        <div className="px-11 py-9 flex flex-col gap-12">
          <div className="flex flex-col gap-6">
            <SettingsInput
              testId="github-token-input"
              onChange={(value) => {
                setGithubTokenInputHasValue(!!value);
              }}
              name="github-token-input"
              label={t(I18nKey.GITHUB$TOKEN_LABEL)}
              type="password"
              className="w-[680px]"
              placeholder={isGitHubTokenSet ? "<hidden>" : ""}
            />

            <GitHubTokenHelpAnchor />
          </div>

          <div className="flex flex-col gap-6">
            <SettingsInput
              testId="gitlab-token-input"
              onChange={(value) => {
                setGitlabTokenInputHasValue(!!value);
              }}
              name="gitlab-token-input"
              label={t(I18nKey.GITLAB$TOKEN_LABEL)}
              type="password"
              className="w-[680px]"
              placeholder={isGitLabTokenSet ? "<hidden>" : ""}
            />

            <GitLabTokenHelpAnchor />
          </div>
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
