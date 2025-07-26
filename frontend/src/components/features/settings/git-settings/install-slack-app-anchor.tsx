import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

export function InstallSlackAppAnchor() {
  const { t } = useTranslation();

  return (
    <div data-testid="install-slack-app-button" className="py-9">
      <BrandButton
        type="button"
        variant="primary"
        className="w-55"
        onClick={() =>
          window.open(
            "https://slack.com/oauth/v2/authorize?client_id=7477886716822.8729519890534&scope=app_mentions:read,chat:write,users:read,channels:history,groups:history,mpim:history,im:history&user_scope=channels:history,groups:history,im:history,mpim:history",
            "_blank",
            "noreferrer noopener",
          )
        }
      >
        {t(I18nKey.SLACK$INSTALL_APP)}
      </BrandButton>
    </div>
  );
}
