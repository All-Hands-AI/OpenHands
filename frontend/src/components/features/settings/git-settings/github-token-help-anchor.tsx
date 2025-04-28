import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="github-token-help-anchor" className="text-xs">
      {t(I18nKey.GITHUB$GET_TOKEN)}{" "}
      <a
        href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
        target="_blank"
        className="font-bold underline underline-offset-2"
        rel="noopener noreferrer"
      >
        GitHub
      </a>{" "}
      {t(I18nKey.COMMON$HERE)}{" "}
      {t(I18nKey.GITLAB$OR_SEE)}{" "}
      <a
        href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
        target="_blank"
        className="font-bold underline underline-offset-2"
        rel="noopener noreferrer"
      >
        {t(I18nKey.COMMON$CLICK_FOR_INSTRUCTIONS)}
      </a>
      .
    </p>
  );
}
