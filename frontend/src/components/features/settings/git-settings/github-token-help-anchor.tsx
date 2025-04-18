import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
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
  );
}
