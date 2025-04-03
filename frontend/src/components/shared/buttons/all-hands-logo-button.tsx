import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { TooltipButton } from "./tooltip-button";

interface AllHandsLogoButtonProps {
  onClick: () => void;
}

export function AllHandsLogoButton({ onClick }: AllHandsLogoButtonProps) {
  const { t } = useTranslation();
  return (
    <TooltipButton
      tooltip={t(I18nKey.BRANDING$ALL_HANDS_AI)}
      ariaLabel={t(I18nKey.BRANDING$ALL_HANDS_LOGO)}
      onClick={onClick}
    >
      <AllHandsLogo width={34} height={34} />
    </TooltipButton>
  );
}
