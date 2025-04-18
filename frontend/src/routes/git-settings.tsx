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

function GitSettingsScreen() {
  const { t } = useTranslation();
  const { mutate: saveSettings } = useSaveSettings();
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
    <form data-testid="git-settings-screen" action={formAction}>
      {isSaas && config.APP_SLUG && (
        <div data-testid="configure-github-repositories-button" />
      )}

      {!isSaas && (
        <>
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
        </>
      )}

      {!isSaas && (
        <>
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
        </>
      )}

      <BrandButton
        testId="submit-button"
        type="submit"
        variant="primary"
        isDisabled={!githubTokenInputHasValue && !gitlabTokenInputHasValue}
      >
        Save Changes
      </BrandButton>
    </form>
  );
}

export default GitSettingsScreen;
