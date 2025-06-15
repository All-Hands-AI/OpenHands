import { Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function BitbucketTokenHelpAnchor() {
  return (
    <p data-testid="bitbucket-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.BITBUCKET$TOKEN_HELP_TEXT}
        components={[
          <a
            key="bitbucket-token-help-anchor-link"
            aria-label="Bitbucket token help link"
            href="https://bitbucket.org/account/settings/app-passwords/new?scopes=repository:write,pullrequest:write,issue:write"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
          <a
            key="bitbucket-token-help-anchor-link-2"
            aria-label="Bitbucket token see more link"
            href="https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
        ]}
      />
    </p>
  );
}
