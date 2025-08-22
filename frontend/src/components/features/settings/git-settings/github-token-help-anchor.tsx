import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="github-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.GITHUB$TOKEN_HELP_TEXT}
        components={[
          <a
            key="github-token-help-anchor-link"
            aria-label={t(I18nKey.GIT$GITHUB_TOKEN_HELP_LINK)}
            href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
          <a
            key="github-token-help-anchor-link-2"
            aria-label={t(I18nKey.GIT$GITHUB_TOKEN_SEE_MORE_LINK)}
            href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
        ]}
      />
    </p>
  );
}
