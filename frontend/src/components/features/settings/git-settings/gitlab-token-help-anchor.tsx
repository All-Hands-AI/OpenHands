import { Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitLabTokenHelpAnchor() {
  return (
    <p data-testid="gitlab-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.GITLAB$TOKEN_HELP_TEXT}
        components={[
          <a
            key="gitlab-token-help-anchor-link"
            aria-label="Gitlab token help link"
            href="https://gitlab.com/-/user_settings/personal_access_tokens?name=openhands-app&scopes=api,read_user,read_repository,write_repository"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
          <a
            key="gitlab-token-help-anchor-link-2"
            aria-label="GitLab token see more link"
            href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
        ]}
      />
    </p>
  );
}
