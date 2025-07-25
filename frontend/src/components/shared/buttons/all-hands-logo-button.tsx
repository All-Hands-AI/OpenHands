import { useTranslation } from "react-i18next";
import AllHandsLogoWhite from "#/assets/branding/all-hands-logo-white.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";

export function AllHandsLogoButton() {
  const { t } = useTranslation();

  return (
    <TooltipButton
      tooltip={t(I18nKey.BRANDING$ALL_HANDS_AI)}
      ariaLabel={t(I18nKey.BRANDING$ALL_HANDS_LOGO)}
      navLinkTo="/"
    >
      <AllHandsLogoWhite width={45.71} height={30} />
    </TooltipButton>
  );
}
