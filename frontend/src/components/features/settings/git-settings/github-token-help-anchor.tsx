import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  const { t } = useTranslation();
  const tokenHelpText = t(I18nKey.GITHUB$TOKEN_HELP_TEXT);
  const parts = tokenHelpText.split(/here/i);

  return (
    <p data-testid="github-token-help-anchor" className="text-xs">
      {parts[0]}
      <a
        href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
        target="_blank"
        className="underline underline-offset-2"
        rel="noopener noreferrer"
      >
        here
      </a>
      {parts[1]}
      <a
        href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
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
