import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitLabTokenHelpAnchor() {
  const { t } = useTranslation();
  const tokenHelpText = t(I18nKey.GITLAB$TOKEN_HELP_TEXT);
  const parts = tokenHelpText.split(/here/i);

  return (
    <p data-testid="gitlab-token-help-anchor" className="text-xs">
      {parts[0]}
      <a
        href="https://gitlab.com/-/user_settings/personal_access_tokens?name=openhands-app&scopes=api,read_user,read_repository,write_repository"
        target="_blank"
        className="underline underline-offset-2"
        rel="noopener noreferrer"
      >
        here
      </a>
      {parts[1]}
      <a
        href="https://docs.gitlab.com/user/profile/personal_access_tokens/"
        target="_blank"
        className="underline underline-offset-2"
        rel="noopener noreferrer"
      >
        here
      </a>
      {parts[2] || ""}
    </p>
  );
}
