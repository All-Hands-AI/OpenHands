import { Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitLabTokenHelpAnchor() {
  return (
    <p data-testid="gitlab-token-help-anchor" className="text-xs">
      <Trans i18nKey={I18nKey.GITLAB$TOKEN_HELP_TEXT}>
        Get your <a
          href="https://gitlab.com/-/user_settings/personal_access_tokens?name=openhands-app&scopes=api,read_user,read_repository,write_repository"
          target="_blank"
          className="underline underline-offset-2"
          rel="noopener noreferrer"
        >
          GitLab token
        </a> or <a
          href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
          target="_blank"
          className="underline underline-offset-2"
          rel="noopener noreferrer"
        >
          click here for instructions
        </a>
      </Trans>
    </p>
  );
}
