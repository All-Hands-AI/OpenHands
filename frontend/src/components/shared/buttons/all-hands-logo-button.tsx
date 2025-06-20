import { useTranslation } from "react-i18next";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import AllHandsLogoWhite from "#/assets/branding/all-hands-logo-white.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";
import { useTheme } from "#/context/theme-context";

export function AllHandsLogoButton() {
  const { t } = useTranslation();
  const { theme } = useTheme();

  return (
    <TooltipButton
      tooltip={t(I18nKey.BRANDING$ALL_HANDS_AI)}
      ariaLabel={t(I18nKey.BRANDING$ALL_HANDS_LOGO)}
      navLinkTo="/"
    >
      {theme === "dark" ? (
        <AllHandsLogoWhite width={34} height={34} />
      ) : (
        <AllHandsLogo width={34} height={34} />
      )}
    </TooltipButton>
  );
}
