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
    <TooltipButton tooltip="Thesis" ariaLabel="Thesis Logo" onClick={onClick}>
      <AllHandsLogo />
    </TooltipButton>
  );
}
