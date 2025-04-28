import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="github-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.GITHUB$TOKEN_HELP_TEXT}
        components={{
          tokenLink: (
            <a
              href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
              target="_blank"
              className="underline underline-offset-2"
              rel="noopener noreferrer"
            >
              {t(I18nKey.GITHUB$TOKEN_LINK_TEXT)}
            </a>
          ),
          instructionsLink: (
            <a
              href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
              target="_blank"
              className="underline underline-offset-2"
              rel="noopener noreferrer"
            >
              {t(I18nKey.GITHUB$INSTRUCTIONS_LINK_TEXT)}
            </a>
          ),
        }}
      />
    </p>
  );
}
