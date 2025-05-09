import { useTranslation } from "react-i18next";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
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
      <AllHandsLogo width={34} height={34} />
    </TooltipButton>
  );
}
