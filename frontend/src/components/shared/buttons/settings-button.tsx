import { useTranslation } from "react-i18next";
import SettingsIcon from "#/icons/settings.svg?react";
import { TooltipButton } from "./tooltip-button";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

interface SettingsButtonProps {
  onClick?: () => void;
  className?: string;
}

export function SettingsButton({ onClick, className }: SettingsButtonProps) {
  const { t } = useTranslation();

  return (
    <TooltipButton
      testId="settings-button"
      tooltip={t(I18nKey.SETTINGS$TITLE)}
      ariaLabel={t(I18nKey.SETTINGS$TITLE)}
      onClick={onClick}
      className={cn(className)}
    >
      <SettingsIcon width={24} height={24} />
    </TooltipButton>
  );
}
