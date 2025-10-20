import { useTranslation } from "react-i18next";
import OpenHandsLogo from "#/assets/branding/openhands-logo.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";

export function OpenHandsLogoButton() {
  const { t } = useTranslation();

  return (
    <TooltipButton
      tooltip={t(I18nKey.BRANDING$OPENHANDS)}
      ariaLabel={t(I18nKey.BRANDING$OPENHANDS_LOGO)}
      navLinkTo="/"
    >
      <OpenHandsLogo width={46} height={30} />
    </TooltipButton>
  );
}
