import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings.svg?react";
import { TooltipButton } from "./tooltip-button";
import { I18nKey } from "#/i18n/declaration";

interface SettingsButtonProps {
  onClick?: () => void;
  disabled?: boolean;
}

export function SettingsButton({
  onClick,
  disabled = false,
}: SettingsButtonProps) {
  const { t } = useTranslation();

  return (
    <TooltipButton
      testId="settings-button"
      tooltip={t(I18nKey.SETTINGS$TITLE)}
      ariaLabel={t(I18nKey.SETTINGS$TITLE)}
      onClick={onClick}
      navLinkTo="/settings"
      disabled={disabled}
    >
      <SettingsIcon width={28} height={28} />
    </TooltipButton>
  );
}
