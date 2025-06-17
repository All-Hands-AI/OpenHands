import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

export function InstallSlackAppAnchor() {
  const { t } = useTranslation();

  return (
    <a
      data-testid="install-slack-app-button"
      href="https://slack.com/oauth/v2/authorize?client_id=7477886716822.8729519890534&scope=app_mentions:read,chat:write,users:read,channels:history,groups:history,mpim:history,im:history&user_scope=channels:history,groups:history,im:history,mpim:history"
      target="_blank"
      rel="noreferrer noopener"
      className="py-9"
    >
      <BrandButton type="button" variant="secondary">
        {t(I18nKey.SLACK$INSTALL_APP)}
      </BrandButton>
    </a>
  );
}
