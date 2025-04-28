import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitHubTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="github-token-help-anchor" className="text-xs">
      Get your{" "}
      <b>
        <a
          href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow"
          target="_blank"
          className="underline underline-offset-2"
          rel="noopener noreferrer"
        >
          GitHub
        </a>{" "}
      </b>
      token here or{" "}
      <b>
        <a
          href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
          target="_blank"
          className="underline underline-offset-2"
          rel="noopener noreferrer"
        >
          click here for instructions
        </a>
      </b>
      .
    </p>
  );
}
