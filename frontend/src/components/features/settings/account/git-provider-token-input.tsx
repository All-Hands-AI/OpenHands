import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { KeyStatusIcon } from "../key-status-icon";
import { SettingsInput } from "../settings-input";

interface GitHubTokenInputProps {
  isGitHubTokenSet: boolean;
}

export function GitHubTokenInput({ isGitHubTokenSet }: GitHubTokenInputProps) {
  const { t } = useTranslation();

  return (
    <>
      <SettingsInput
        testId="github-token-input"
        name="github-token-input"
        label={t(I18nKey.GITHUB$TOKEN_LABEL)}
        type="password"
        className="w-[680px]"
        startContent={
          isGitHubTokenSet && <KeyStatusIcon isSet={!!isGitHubTokenSet} />
        }
        placeholder={isGitHubTokenSet ? "<hidden>" : ""}
      />
      <p data-testid="github-token-help-anchor" className="text-xs">
        {" "}
        {t(I18nKey.GITHUB$GET_TOKEN)}{" "}
        <b>
          {" "}
          <a
            href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          >
            GitHub
          </a>{" "}
        </b>
        {t(I18nKey.COMMON$HERE)}{" "}
        <b>
          <a
            href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          >
            {t(I18nKey.COMMON$CLICK_FOR_INSTRUCTIONS)}
          </a>
        </b>
        .
      </p>
    </>
  );
}

interface GitLabTokenInputProps {
  isGitLabTokenSet: boolean;
}

export function GitLabTokenInput({ isGitLabTokenSet }: GitLabTokenInputProps) {
  const { t } = useTranslation();

  return (
    <>
      <SettingsInput
        testId="gitlab-token-input"
        name="gitlab-token-input"
        label={t(I18nKey.GITHUB$TOKEN_LABEL)}
        type="password"
        className="w-[680px]"
        startContent={
          isGitLabTokenSet && <KeyStatusIcon isSet={!!isGitLabTokenSet} />
        }
        placeholder={isGitLabTokenSet ? "<hidden>" : ""}
      />

      <p data-testid="gitlab-token-help-anchor" className="text-xs">
        {" "}
        {t(I18nKey.GITHUB$GET_TOKEN)}{" "}
        <b>
          {" "}
          <a
            href="https://gitlab.com/-/user_settings/personal_access_tokens?name=openhands-app&scopes=api,read_user,read_repository,write_repository"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          >
            GitLab
          </a>{" "}
        </b>
        {t(I18nKey.GITLAB$OR_SEE)}{" "}
        <b>
          <a
            href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          >
            {t(I18nKey.COMMON$CLICK_FOR_INSTRUCTIONS)}
          </a>
        </b>
        .
      </p>
    </>
  );
}
