import { Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  return (
    <p data-testid="github-token-help-anchor" className="text-xs">
      <Trans i18nKey={I18nKey.GITHUB$TOKEN_HELP_TEXT}>
        Get your <a
          href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
          target="_blank"
          className="underline underline-offset-2"
          rel="noopener noreferrer"
        >
          GitHub token
        </a> or <a
          href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
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
