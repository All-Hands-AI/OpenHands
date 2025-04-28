import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitLabTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="gitlab-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.GITLAB$TOKEN_HELP_TEXT}
        components={{
          tokenLink: (
            <a
              href="https://gitlab.com/-/user_settings/personal_access_tokens?name=openhands-app&scopes=api,read_user,read_repository,write_repository"
              target="_blank"
              className="underline underline-offset-2"
              rel="noopener noreferrer"
            >
              {t(I18nKey.GITLAB$TOKEN_LINK_TEXT)}
            </a>
          ),
          instructionsLink: (
            <a
              href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
              target="_blank"
              className="underline underline-offset-2"
              rel="noopener noreferrer"
            >
              {t(I18nKey.GITLAB$INSTRUCTIONS_LINK_TEXT)}
            </a>
          ),
        }}
      />
    </p>
  );
}
