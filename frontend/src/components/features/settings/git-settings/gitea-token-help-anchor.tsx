import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GiteaTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="gitea-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.GITEA$TOKEN_HELP_TEXT}
        components={[
          <a
            key="gitea-token-help-anchor-link"
            aria-label={t(I18nKey.GIT$GITEA_TOKEN_HELP_LINK)}
            href="https://docs.gitea.com/development/api-usage#authentication"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
          <a
            key="gitea-token-help-anchor-link-2"
            aria-label={t(I18nKey.GIT$GITEA_TOKEN_SEE_MORE_LINK)}
            href="https://docs.gitea.com/usage/api-usage"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
        ]}
      />
    </p>
  );
}
